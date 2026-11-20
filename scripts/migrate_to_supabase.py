"""
migrate_to_supabase.py
======================
Executes Alembic migrations against Supabase PostgreSQL and performs
immediate post-migration schema verification.

SAFETY CONSTRAINTS:
1. Strictly refuses to run against SQLite or localhost.
2. Uses verified DATABASE_URL from environment or prompts for password via hidden input.
3. Explicitly verifies target host is aws-0-ap-southeast-1.pooler.supabase.com, db is postgres, port is 5432.
4. Explicitly verifies SQLAlchemy dialect is 'postgresql'.
5. Passes the active verified SQLAlchemy connection via config.attributes["connection"] to Alembic.
6. Immune to ConfigParser percent-encoding bugs (handles %, @, #, :, etc. safely).
7. Never reports success unless target PostgreSQL database actually reaches revision b6f49c365d8f.
8. Sanitizes all error messages so raw credentials never appear in outputs or logs.
9. Does NOT modify or touch the original SQLite database or backups.
10. Does NOT create an admin account or insert persistent user data.
"""
import os
import sys
import re
from pathlib import Path
from urllib.parse import urlparse

# Add backend and scripts to sys.path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
root_dir = Path(__file__).resolve().parent.parent
scripts_dir = Path(__file__).resolve().parent

if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

from db_connection_helper import get_supabase_url, mask_url, sanitize_error
from verify_supabase_migration import verify_supabase_schema

print("=" * 65)
print("RoofwiseBD — Supabase PostgreSQL Migration Runner")
print("=" * 65)

# Step 1: Securely obtain verified Supabase DATABASE_URL
DATABASE_URL = get_supabase_url()

if "sqlite" in DATABASE_URL.lower():
    print("[ABORT] DATABASE_URL points to SQLite. Migration requires PostgreSQL.")
    sys.exit(1)

if not (DATABASE_URL.startswith("postgresql://") or DATABASE_URL.startswith("postgres://")):
    print("[ABORT] DATABASE_URL does not look like a PostgreSQL connection string.")
    sys.exit(1)

masked_url = mask_url(DATABASE_URL)
print(f"\n[TARGET] Verified Supabase Target: {masked_url}")

# Step 2: Pre-migration Target Host, Port, and Database Verification
parsed = urlparse(masked_url)
target_host = parsed.hostname
target_port = parsed.port or 5432
target_db = parsed.path.lstrip("/") or "postgres"

print("\n[Step 1/4] Verifying Target Infrastructure Parameters...")
print(f"  Target Host:     {target_host}")
print(f"  Target Port:     {target_port}")
print(f"  Target Database: {target_db}")

expected_host = "aws-0-ap-southeast-1.pooler.supabase.com"
expected_db = "postgres"
expected_port = 5432

if target_host != expected_host:
    print(f"[FAIL] Target host mismatch: expected '{expected_host}', got '{target_host}'")
    sys.exit(1)
if target_port != expected_port:
    print(f"[FAIL] Target port mismatch: expected {expected_port}, got {target_port}")
    sys.exit(1)
if target_db != expected_db:
    print(f"[FAIL] Target database mismatch: expected '{expected_db}', got '{target_db}'")
    sys.exit(1)
print("[OK] Infrastructure parameters match verified Supabase project.")

# Step 3: Test PostgreSQL connection & SQLAlchemy Dialect
print("\n[Step 2/4] Testing PostgreSQL connectivity & dialect...")
try:
    import sqlalchemy as sa
    db_url = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    engine = sa.create_engine(db_url, pool_pre_ping=True, connect_args={"connect_timeout": 15})
    
    if engine.dialect.name != "postgresql":
        print(f"[FAIL] Expected dialect 'postgresql', got '{engine.dialect.name}'")
        sys.exit(1)
    print(f"[OK] Connection dialect verified: {engine.dialect.name} (driver: {engine.dialect.driver})")

    with engine.connect() as conn:
        result = conn.execute(sa.text("SELECT version()"))
        pg_version = result.fetchone()[0]
    print(f"[OK] Connected to PostgreSQL: {pg_version[:65]}...")
except Exception as e:
    sanitized_err = sanitize_error(e, DATABASE_URL)
    print(f"[FAIL] Cannot connect to PostgreSQL: {sanitized_err}")
    sys.exit(1)

# Step 4: Run Alembic migration passing the active connection directly
print("\n[Step 3/4] Applying Alembic schema migration (alembic upgrade head)...")
ini_path = (backend_dir / "alembic.ini").resolve()
alembic_script_dir = (backend_dir / "alembic").resolve()

print(f"  Configuration File: {ini_path}")
print(f"  Script Location:    {alembic_script_dir}")

from alembic.config import Config
from alembic import command

cfg = Config(str(ini_path))
cfg.set_main_option("script_location", str(alembic_script_dir))
# Pass safely escaped URL for ConfigParser interpolation protection
cfg.set_main_option("sqlalchemy.url", re.sub(r'%(?!%)', '%%', DATABASE_URL))

try:
    with engine.connect() as connection:
        cfg.attributes["connection"] = connection
        command.upgrade(cfg, "head")
    print("[OK] Alembic migration finished successfully.")
except Exception as e:
    sanitized_err = sanitize_error(e, DATABASE_URL)
    print(f"[FAIL] Alembic migration failed: {sanitized_err}")
    sys.exit(1)

# Step 5: Post-migration Head Verification & Schema Check
print("\n[Step 4/4] Verifying PostgreSQL target actually reached revision b6f49c365d8f...")
try:
    with engine.connect() as conn:
        row = conn.execute(sa.text("SELECT version_num FROM alembic_version;")).fetchone()
        actual_rev = row[0] if row else None
    
    if actual_rev != "b6f49c365d8f":
        print(f"\n[FATAL ERROR] Target PostgreSQL alembic_version is '{actual_rev}', expected 'b6f49c365d8f'!")
        print("Migration was NOT applied to the target database. Aborting.")
        sys.exit(1)
    print(f"[OK] Confirmed: PostgreSQL reached Alembic head revision '{actual_rev}'")
except Exception as e:
    sanitized_err = sanitize_error(e, DATABASE_URL)
    print(f"\n[FATAL ERROR] Could not verify alembic_version in PostgreSQL: {sanitized_err}")
    sys.exit(1)

# Step 6: Run comprehensive post-migration verification
verification_passed = verify_supabase_schema(DATABASE_URL)

if not verification_passed:
    print("\n[FAIL] Post-migration schema verification failed!")
    sys.exit(1)

print("\n" + "=" * 65)
print("[SUCCESS] SUPABASE SCHEMA MIGRATION & VERIFICATION COMPLETE")
print("=" * 65)
print("All 5 tables, 31 assessment columns, foreign keys, unique constraints,")
print("indexes, and alembic revision b6f49c365d8f have been verified on Supabase.")
print("\n[STOP] Paused according to instructions. No admin account has been created.")
print("Waiting for explicit approval before proceeding to admin account provisioning.")
print("=" * 65)
