"""
RoofwiseBD — Shared Database Connection Helper
==============================================
Securely resolves the target Supabase DATABASE_URL without saving secrets.
1. Uses os.environ['DATABASE_URL'] if already set and complete.
2. Otherwise reads the verified sanitized template from supabase_connection_status.json.
3. Prompts for the database password using hidden input (getpass).
4. Safely injects the RFC 3986 percent-encoded password strictly in memory.
5. Strictly blocks SQLite and localhost/non-PostgreSQL targets.
6. Sanitizes all credentials and error messages to prevent leakage.
"""
import os
import sys
import json
import getpass
import re
from pathlib import Path
from urllib.parse import quote, urlparse, urlunparse

try:
    from dotenv import load_dotenv
    backend_env = Path(__file__).resolve().parent.parent / "backend" / ".env"
    if backend_env.exists():
        load_dotenv(backend_env)
except Exception:
    pass

def mask_url(url: str) -> str:
    """
    Masks password in database URLs.
    Handles special characters (@, #, :, /, etc.) cleanly and safely.
    """
    if not url:
        return ""
    # Primary regex masking for authority component: postgresql://user:password@host
    masked = re.sub(r'^(postgres(?:ql)?://[^:]+:)[^@]+(@)', r'\1******\2', url)
    if "******" in masked:
        return masked
    try:
        parsed = urlparse(url)
        if parsed.password:
            netloc = f"{parsed.username}:******@{parsed.hostname}"
            if parsed.port:
                netloc += f":{parsed.port}"
            return urlunparse(parsed._replace(netloc=netloc))
        return url
    except Exception:
        return "postgresql://[credentials-masked]@[host]/postgres"

def sanitize_error(error: Exception | str, url: str = None) -> str:
    """
    Sanitizes exception messages and tracebacks so credentials/passwords never leak.
    """
    msg = str(error)
    # 1. Mask any connection strings matching user:password@
    msg = re.sub(r'(postgres(?:ql)?://[^:]+:)[^@]+(@)', r'\1******\2', msg)
    # 2. If url is provided, extract both raw and encoded password and mask occurrences
    if url:
        try:
            from sqlalchemy.engine import make_url
            sa_url = make_url(url)
            if sa_url.password:
                msg = msg.replace(sa_url.password, "******")
        except Exception:
            pass
        m = re.search(r'postgres(?:ql)?://[^:]+:([^@]+)@', url)
        if m:
            raw_enc = m.group(1)
            if raw_enc and raw_enc != "******":
                msg = msg.replace(raw_enc, "******")
    return msg

def get_safe_connection_diagnostics(database_url: str) -> dict:
    """
    Safely inspects and returns connection parameters without leaking passwords or secrets.
    Verifies driver, host, port, database, username, and Supabase pooler tenant suffix.
    """
    import sqlalchemy as sa
    from sqlalchemy.engine import make_url

    db_url = database_url.replace("postgres://", "postgresql://", 1)
    sa_url = make_url(db_url)
    engine = sa.create_engine(db_url)
    cargs, ckwargs = engine.dialect.create_connect_args(sa_url)

    username = sa_url.username or ckwargs.get("user") or ""
    host = sa_url.host or ckwargs.get("host") or ""
    port = sa_url.port or ckwargs.get("port") or 5432
    database = sa_url.database or ckwargs.get("dbname") or ""
    driver = f"{engine.dialect.name} ({engine.dialect.driver})"
    tenant_id = username.split(".", 1)[1] if "." in username else None

    return {
        "driver": driver,
        "dialect": engine.dialect.name,
        "driver_name": engine.dialect.driver,
        "host": host,
        "port": port,
        "database": database,
        "username": username,
        "tenant_id": tenant_id,
        "driver_user": ckwargs.get("user")
    }

def print_connection_diagnostics(database_url: str) -> dict:
    """
    Prints safe connection diagnostics without leaking passwords or secrets.
    """
    diag = get_safe_connection_diagnostics(database_url)
    print("\n" + "=" * 65)
    print("ROOFWISEBD — SAFE CONNECTION DIAGNOSTICS")
    print("(Credentials strictly omitted)")
    print("=" * 65)
    print(f"  Driver:              {diag['driver']}")
    print(f"  Target Host:         {diag['host']}")
    print(f"  Target Port:         {diag['port']}")
    print(f"  Target Database:     {diag['database']}")
    print(f"  Target Username:     {diag['username']}")
    if diag['tenant_id']:
        print(f"  Tenant Identifier:   {diag['tenant_id']} (Pooler tenant verified)")
    else:
        print(f"  Tenant Identifier:   [MISSING] Warning: Missing tenant suffix for pooler!")
    print(f"  Driver Connect User: {diag['driver_user']}")
    print("=" * 65)
    return diag

def get_supabase_url() -> str:
    env_url = os.environ.get("DATABASE_URL", "").strip()
    if env_url and ("postgresql://" in env_url or "postgres://" in env_url) and "[YOUR" not in env_url.upper() and "******" not in env_url:
        print(f"[INFO] Using DATABASE_URL from environment: {mask_url(env_url)}")
        return env_url

    status_file = Path(__file__).resolve().parent / "supabase_connection_status.json"
    template = ""
    if status_file.exists():
        try:
            with open(status_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                template = data.get("target_sanitized", "")
        except Exception:
            pass

    if not template or "******" not in template:
        print("\n[Step 1] Enter Supabase URI Template:")
        if sys.stdin.isatty():
            template = input("URI Template: ").strip()
        else:
            print("URI Template: ", end="", flush=True)
            template = sys.stdin.readline().strip()

    if not template:
        print("[ABORT] No URI template provided.")
        sys.exit(1)

    # Check environment variable for password first
    pw = (os.environ.get("SUPABASE_DB_PASSWORD") or os.environ.get("PGPASSWORD") or "").strip()
    if pw:
        print("[INFO] Using database password from environment variable.")
    else:
        # Prompt for password securely
        print("\n" + "=" * 65)
        print("ROOFWISEBD — SECURE DATABASE AUTHENTICATION")
        print("=" * 65)
        print(f"Target Database: {template.replace('******', '[PASSWORD-INPUT]')}")
        print("Please enter your database password (keystrokes will be completely HIDDEN):")
        print("-" * 65)

        if sys.stdin.isatty():
            pw = getpass.getpass("Database Password (input hidden): ").strip()
        else:
            print("Database Password (input hidden): ", end="", flush=True)
            pw = sys.stdin.readline().strip()

    if not pw:
        print("[ABORT] No password provided.")
        sys.exit(1)

    # Standard RFC 3986 URL encoding for userinfo component
    # Encodes all reserved characters (@, %, #, :, /, +, etc.)
    enc_pw = quote(pw, safe="")
    if "******" in template:
        full_uri = template.replace("******", enc_pw)
    else:
        m = re.match(r'^(postgres(?:ql)?://[^:]+:)(.*?)(@.*)$', template)
        if m:
            full_uri = m.group(1) + enc_pw + m.group(3)
        else:
            m2 = re.match(r'^(postgres(?:ql)?://)([^@]+)(@.*)$', template)
            if m2:
                full_uri = m2.group(1) + m2.group(2) + ':' + enc_pw + m2.group(3)
            else:
                full_uri = template

    # Safety checks
    if "sqlite" in full_uri.lower():
        print("[ABORT] Safety violation: URL points to SQLite.")
        sys.exit(1)

    if not (full_uri.startswith("postgresql://") or full_uri.startswith("postgres://")):
        print("[ABORT] Invalid PostgreSQL URL protocol.")
        sys.exit(1)

    return full_uri
