"""
RoofwiseBD — Supabase PostgreSQL Read-Only Connectivity Verification
===================================================================
BEGINNER-FRIENDLY TWO-STEP SECURE INPUT:
1. Prompts for the URI Template (with [YOUR-DATABASE-PASSWORD] placeholder).
2. Prompts separately for the database password using hidden input (getpass).
3. Automatically URL-encodes the password and constructs the full connection URI in memory.
4. Strictly read-only: executes only diagnostic metadata queries.
5. Never logs, displays, or saves the password or complete raw URI.
6. Does NOT run migrations or create any admin account.
7. Does NOT touch SQLite or any backups.
"""
import os
import sys
import re
import getpass
from urllib.parse import urlparse, urlunparse, quote_plus
import json
from pathlib import Path

# Add backend to sys.path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

def mask_connection_string(uri: str, password: str = None) -> str:
    """Masks password in connection URI for safe display and logging."""
    try:
        # If raw password known, replace it directly first
        if password:
            uri = uri.replace(quote_plus(password), "******").replace(password, "******")
        parsed = urlparse(uri)
        if parsed.password:
            netloc = f"{parsed.username}:******@{parsed.hostname}"
            if parsed.port:
                netloc += f":{parsed.port}"
            return urlunparse(parsed._replace(netloc=netloc))
        return uri
    except Exception:
        return "postgresql://[credentials-masked]@[host]/postgres"

def build_connection_uri(template: str, password: str) -> str:
    """Safely injects URL-encoded password into URI template."""
    enc_pw = quote_plus(password)
    clean_template = template.strip()

    # Pattern 1: scheme://user:placeholder@host...
    m = re.match(r'^(postgres(?:ql)?://[^:]+:)(.*?)(@.*)$', clean_template)
    if m:
        prefix, old_pw, suffix = m.groups()
        return prefix + enc_pw + suffix

    # Pattern 2: scheme://user@host... (no password separator)
    m2 = re.match(r'^(postgres(?:ql)?://)([^@]+)(@.*)$', clean_template)
    if m2:
        scheme, user, suffix = m2.groups()
        return scheme + user + ':' + enc_pw + suffix

    raise ValueError(
        "Invalid URI format. Expected format: "
        "postgresql://postgres.[project-ref]:[YOUR-PASSWORD]@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres"
    )

def prompt_input(prompt_text: str, hidden: bool = False) -> str:
    """Reads input securely via getpass or stdin depending on tty."""
    if hidden:
        try:
            if sys.stdin.isatty():
                return getpass.getpass(prompt_text).strip()
            else:
                print(prompt_text, end="", flush=True)
                return sys.stdin.readline().strip()
        except Exception as e:
            print(f"[ERROR] Could not read hidden input: {e}")
            sys.exit(1)
    else:
        print(prompt_text, end="", flush=True)
        return sys.stdin.readline().strip()

def get_connection_uri() -> tuple[str, str]:
    """Retrieves URI template and password in two beginner-friendly steps."""
    # Check if complete DATABASE_URL is already in environment
    env_uri = os.environ.get("DATABASE_URL", "").strip()
    if env_uri and "[YOUR" not in env_uri.upper():
        print("[INFO] Found complete DATABASE_URL in environment variable.")
        return env_uri, ""

    print("\n" + "=" * 70)
    print("ROOFWISEBD — SECURE SUPABASE CONNECTION SETUP")
    print("=" * 70)
    print("We will connect to your Supabase PostgreSQL database in 2 easy steps:")
    print("  Step 1: Paste the URI template (with [YOUR-DATABASE-PASSWORD] placeholder).")
    print("  Step 2: Enter your database password separately (keystrokes hidden).")
    print("=" * 70)

    # Step 1: URI Template
    print("\n[Step 1 of 2] Paste your Supabase URI template:")
    template = prompt_input("URI Template: ", hidden=False)
    if not template:
        print("[ABORT] No URI template provided.")
        sys.exit(1)

    if "sqlite" in template.lower():
        print("[ABORT] URL points to SQLite. Expected PostgreSQL.")
        sys.exit(1)

    if not (template.startswith("postgresql://") or template.startswith("postgres://")):
        print("[ABORT] Invalid protocol. URI must start with 'postgresql://' or 'postgres://'")
        sys.exit(1)

    # Step 2: Password
    print("\n[Step 2 of 2] Enter your Supabase database password:")
    print("(NOTE: Characters will NOT appear on screen while typing/pasting)")
    password = prompt_input("Database Password (input hidden): ", hidden=True)
    if not password:
        print("[ABORT] No password provided.")
        sys.exit(1)

    # Construct complete URI
    try:
        full_uri = build_connection_uri(template, password)
    except ValueError as ve:
        print(f"[ABORT] {ve}")
        sys.exit(1)

    return full_uri, password

def verify_connection():
    full_uri, raw_password = get_connection_uri()

    masked_uri = mask_connection_string(full_uri, raw_password)
    print(f"\n[TARGET] Connecting to: {masked_uri}")

    import sqlalchemy as sa
    from sqlalchemy import text

    # Normalize protocol for SQLAlchemy
    sqlalchemy_url = full_uri
    if sqlalchemy_url.startswith("postgres://"):
        sqlalchemy_url = sqlalchemy_url.replace("postgres://", "postgresql://", 1)

    print("\n[Step 1/4] Establishing secure SSL connection to Supabase PostgreSQL...")
    engine = sa.create_engine(
        sqlalchemy_url,
        connect_args={"connect_timeout": 15},
        pool_pre_ping=True
    )

    parsed = urlparse(masked_uri)
    host = parsed.hostname
    port = parsed.port or 5432

    try:
        with engine.connect() as conn:
            print("[Step 2/4] Connection established successfully! Running diagnostic checks...")

            # 1. PostgreSQL version
            version_str = conn.execute(text("SELECT version();")).scalar()

            # 2. Database and user
            row = conn.execute(text(
                "SELECT current_database(), current_user, current_setting('server_version');"
            )).fetchone()
            curr_db, curr_user, srv_ver = row[0], row[1], row[2]

            # 3. SSL status
            ssl_status = conn.execute(text("SELECT current_setting('ssl');")).scalar()

            # 4. Existing public tables (read-only audit)
            print("[Step 3/4] Inspecting public schema tables...")
            tables_result = conn.execute(text(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public' ORDER BY table_name;"
            )).fetchall()
            public_tables = [r[0] for r in tables_result]

            # 5. Server time
            srv_time = conn.execute(text("SELECT NOW();")).scalar()

            print("[Step 4/4] Diagnostics completed successfully.")

            print("\n" + "=" * 70)
            print("SUPABASE CONNECTIVITY VERIFICATION: PASSED (READ-ONLY)")
            print("=" * 70)
            print(f"  Hostname:           {host}")
            print(f"  Port:               {port}")
            print(f"  Database Name:      {curr_db}")
            print(f"  Database User:      {curr_user}")
            print(f"  PostgreSQL Version: {srv_ver}")
            print(f"  SSL Encryption:     {'ENABLED (' + ssl_status + ')' if ssl_status == 'on' else ssl_status}")
            print(f"  Server Timestamp:   {srv_time}")
            print(f"  Full Version:       {version_str[:70]}...")
            print(f"  Existing Tables:    {public_tables if public_tables else '0 tables (Clean Database)'}")
            print("=" * 70)

            # Export sanitized JSON status file for inspection (no secrets!)
            status_file = Path(__file__).resolve().parent / "supabase_connection_status.json"
            status_data = {
                "status": "connected",
                "hostname": host,
                "port": port,
                "database": curr_db,
                "user": curr_user,
                "postgresql_version": srv_ver,
                "ssl_enabled": ssl_status == "on",
                "existing_public_tables": public_tables,
                "target_sanitized": masked_uri,
                "server_time": str(srv_time)
            }
            with open(status_file, "w", encoding="utf-8") as f:
                json.dump(status_data, f, indent=2)
            print(f"[OK] Sanitized report saved to {status_file.name} (zero credentials contained).")
            print("\n[READY] Supabase database is verified, healthy, and ready for Alembic migration.")
            print("[REMINDER] No migrations have been run. No changes made. Waiting for approval.")

    except Exception as exc:
        print("\n" + "=" * 70)
        print("[FAIL] Connection verification failed.")
        print("=" * 70)
        err_msg = str(exc)
        if raw_password:
            err_msg = err_msg.replace(quote_plus(raw_password), "******").replace(raw_password, "******")
        print(f"Error details: {err_msg}")
        print("\nTroubleshooting tips:")
        print("1. Did you enter the correct database password in Step 2?")
        print("2. Ensure you are using the Session Pooler (port 5432) or Transaction Pooler (port 6543) if your ISP lacks IPv6.")
        print("3. Check that your Supabase project status is 'Active' / 'Healthy' in the dashboard.")
        sys.exit(1)

if __name__ == "__main__":
    verify_connection()
