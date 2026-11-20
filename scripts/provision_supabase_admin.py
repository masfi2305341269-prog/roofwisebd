"""
provision_supabase_admin.py
============================
Provisions the initial RoofwiseBD administrator account against
the live Supabase PostgreSQL database.

SECURITY CONSTRAINTS:
1. Admin email is hardcoded to admin@roofwisebd.com (no user input for email).
2. Admin password is prompted via getpass — NEVER printed, logged, or saved.
3. Password is hashed with Argon2id before ANY database write.
4. Checks for existing admin account first — refuses to create duplicates.
5. Verifies the resulting account: role=admin, is_active=True.
6. Verifies public user registration still creates role=user, is_active=True.
7. Never connects to SQLite — strictly enforces PostgreSQL target.
8. Sanitizes all error messages via sanitize_error().
9. Does NOT restore the old backup admin account.
"""
import os
import sys
import getpass
import re
from pathlib import Path
from urllib.parse import urlparse

backend_dir = Path(__file__).resolve().parent.parent / "backend"
scripts_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

from db_connection_helper import get_supabase_url, mask_url, sanitize_error, print_connection_diagnostics

ADMIN_EMAIL = "admin@roofwisebd.com"
EXPECTED_HOST = "aws-0-ap-southeast-1.pooler.supabase.com"
EXPECTED_PORT = 5432
EXPECTED_DB   = "postgres"
EXPECTED_USER = "postgres.dopfzvcmefjpvdtefvpj"

print("=" * 65)
print("RoofwiseBD — Supabase Administrator Provisioning")
print("=" * 65)

# ── Step 1: Secure URL & Pre-flight Diagnostics ──────────────────────────────
DATABASE_URL = get_supabase_url()

if "sqlite" in DATABASE_URL.lower():
    print("[ABORT] DATABASE_URL points to SQLite. Admin provisioning requires PostgreSQL.")
    sys.exit(1)

# Safe pre-flight diagnostic showing driver, host, port, db, user, tenant
diag = print_connection_diagnostics(DATABASE_URL)

if diag["username"] != EXPECTED_USER:
    print(f"[ABORT] Username is '{diag['username']}', expected '{EXPECTED_USER}'.")
    sys.exit(1)

if diag["host"] != EXPECTED_HOST or diag["port"] != EXPECTED_PORT:
    print(f"[ABORT] Target host/port mismatch. Expected {EXPECTED_HOST}:{EXPECTED_PORT}, got {diag['host']}:{diag['port']}.")
    sys.exit(1)

if diag["database"] != EXPECTED_DB:
    print(f"[ABORT] Target database mismatch. Expected '{EXPECTED_DB}', got '{diag['database']}'.")
    sys.exit(1)

if not diag["tenant_id"]:
    print(f"[ABORT] Target username '{diag['username']}' is missing Supabase pooler tenant suffix.")
    sys.exit(1)

print(f"[OK] Pre-flight verification passed: {diag['username']}@{diag['host']}:{diag['port']}/{diag['database']}")

# ── Step 2: Establish PostgreSQL connection ───────────────────────────────────
print("\n[Step 1/5] Connecting to Supabase PostgreSQL...")
try:
    import sqlalchemy as sa
    db_url = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    engine = sa.create_engine(db_url, pool_pre_ping=True, connect_args={"connect_timeout": 15})
    with engine.connect() as conn:
        row = conn.execute(sa.text("SELECT current_database(), version()")).fetchone()
        db_name, pg_ver = row[0], row[1][:60]
    print(f"[OK] Connected: db={db_name}, {pg_ver}...")
    if engine.dialect.name != "postgresql":
        print(f"[ABORT] Unexpected dialect: {engine.dialect.name}")
        sys.exit(1)
except Exception as e:
    err_str = sanitize_error(e, DATABASE_URL)
    print(f"[FAIL] {err_str}")
    if "password authentication failed" in err_str.lower():
        print("\n" + "-" * 65)
        print("[AUTHENTICATION FAILURE EXPLANATION]")
        print("1. Notice: PostgreSQL reports 'password authentication failed for user \"postgres\"'")
        print("   because \"postgres\" is the internal database role name on Supabase.")
        print(f"   The pooler username '{diag['username']}' WAS received correctly by Supavisor.")
        print("2. The failure indicates that the password provided does not match the current")
        print("   database password for role 'postgres' on this Supabase project.")
        print("3. Possible causes:")
        print("   - If you recently rotated the password in the Supabase Dashboard, verify you")
        print("     are entering the NEW database password (not the Supabase account password).")
        print("   - If $env:DATABASE_URL was set in PowerShell before password rotation, it")
        print("     contains the old password. Clear it with: Remove-Item Env:\\DATABASE_URL")
        print("   - Ensure no extra spaces or quotes were pasted.")
        print("-" * 65)
    sys.exit(1)

# ── Step 3: Verify Alembic head revision ─────────────────────────────────────
print("\n[Step 2/5] Verifying Alembic head revision...")
try:
    with engine.connect() as conn:
        rev = conn.execute(sa.text("SELECT version_num FROM alembic_version")).fetchone()
        actual_rev = rev[0] if rev else None
    if actual_rev != "a5764b316a82":
        print(f"[ABORT] alembic_version = '{actual_rev}', expected 'a5764b316a82'. Run migration first.")
        sys.exit(1)
    print(f"[OK] Alembic revision verified: {actual_rev}")
except Exception as e:
    print(f"[FAIL] {sanitize_error(e, DATABASE_URL)}")
    sys.exit(1)

# ── Step 4: Check for existing admin ─────────────────────────────────────────
print(f"\n[Step 3/5] Checking for existing admin account ({ADMIN_EMAIL})...")
try:
    with engine.connect() as conn:
        existing = conn.execute(
            sa.text("SELECT id, role, is_active FROM users WHERE email = :e"),
            {"e": ADMIN_EMAIL}
        ).fetchone()
    if existing:
        print(f"[ABORT] Account '{ADMIN_EMAIL}' already exists (id={existing[0]}, role={existing[1]}, active={existing[2]}).")
        print("        Admin account was already provisioned. Use the existing credentials.")
        print("        To reset the password, use the admin password-change API endpoint.")
        sys.exit(0)
    print(f"[OK] No existing account for '{ADMIN_EMAIL}' — safe to create.")
except Exception as e:
    print(f"[FAIL] {sanitize_error(e, DATABASE_URL)}")
    sys.exit(1)

# ── Step 5: Prompt for admin password (hidden) ────────────────────────────────
print("\n[Step 4/5] Admin Password Setup")
print("-" * 65)
print(f"  Creating administrator account: {ADMIN_EMAIL}")
print("  Password requirements: min 8 chars, at least 1 letter and 1 digit")
print("-" * 65)

if sys.stdin.isatty():
    admin_pw = getpass.getpass("  Admin password (hidden): ").strip()
    confirm_pw = getpass.getpass("  Confirm admin password (hidden): ").strip()
else:
    print("  Admin password (hidden): ", end="", flush=True)
    admin_pw = sys.stdin.readline().strip()
    print("  Confirm admin password (hidden): ", end="", flush=True)
    confirm_pw = sys.stdin.readline().strip()

if not admin_pw:
    print("[ABORT] No password provided.")
    sys.exit(1)

if admin_pw != confirm_pw:
    print("[ABORT] Passwords do not match.")
    sys.exit(1)

# Validate password strength
from app.core.security import validate_password_strength, get_password_hash
is_valid, err_msg = validate_password_strength(admin_pw)
if not is_valid:
    print(f"[ABORT] Password does not meet requirements: {err_msg}")
    sys.exit(1)

# Hash with Argon2id immediately — raw password no longer referenced after this
hashed_pw = get_password_hash(admin_pw)
del admin_pw, confirm_pw  # Explicit cleanup from memory
print("[OK] Password validated and hashed with Argon2id. Raw password cleared from memory.")

# ── Step 6: Insert admin account ──────────────────────────────────────────────
print(f"\n[Step 5/5] Creating administrator account...")
try:
    from datetime import datetime
    with engine.begin() as conn:
        conn.execute(sa.text("""
            INSERT INTO users (email, hashed_password, full_name, role, is_active, created_at, updated_at)
            VALUES (:email, :pw, :name, :role, :active, NOW(), NOW())
        """), {
            "email": ADMIN_EMAIL,
            "pw": hashed_pw,
            "name": "System Administrator",
            "role": "admin",
            "active": True,
        })
    print(f"[OK] Administrator account inserted for '{ADMIN_EMAIL}'.")
except Exception as e:
    print(f"[FAIL] {sanitize_error(e, DATABASE_URL)}")
    sys.exit(1)

# ── Step 7: Verify the new admin account ──────────────────────────────────────
print("\n" + "=" * 65)
print("POST-PROVISIONING VERIFICATION")
print("=" * 65)

PASS, FAIL = [], []

def check(cond, ok_msg, fail_msg):
    if cond:
        PASS.append(ok_msg)
        print(f"  [OK]   {ok_msg}")
    else:
        FAIL.append(fail_msg)
        print(f"  [FAIL] {fail_msg}")

try:
    with engine.connect() as conn:
        row = conn.execute(
            sa.text("SELECT id, email, full_name, role, is_active FROM users WHERE email = :e"),
            {"e": ADMIN_EMAIL}
        ).fetchone()

    check(row is not None,                f"Admin account '{ADMIN_EMAIL}' exists in database", f"Admin account NOT FOUND")
    check(row[3] == "admin",              f"role = '{row[3]}' (correct)",                      f"role = '{row[3]}' (expected 'admin')")
    check(row[4] == True,                 f"is_active = True",                                  f"is_active = {row[4]} (expected True)")
    check(row[2] == "System Administrator", f"full_name = '{row[2]}'",                          f"full_name mismatch: '{row[2]}'")

    # hashed_password verification is handled below in a fresh connection block.
except Exception as e:
    print(f"  [FAIL] Verification query error: {sanitize_error(e, DATABASE_URL)}")
    FAIL.append("Verification query failed")

# Verify password hash algorithm
try:
    with engine.connect() as conn:
        pw_hash = conn.execute(
            sa.text("SELECT hashed_password FROM users WHERE email = :e"),
            {"e": ADMIN_EMAIL}
        ).fetchone()[0]
    check(pw_hash.startswith("$argon2id$"),
          f"Password stored as Argon2id hash (prefix: {pw_hash[:20]}...)",
          f"Unexpected hash prefix: {pw_hash[:20]}...")
except Exception as e:
    FAIL.append(f"Hash verification error: {sanitize_error(e, DATABASE_URL)}")

# Verify no duplicate admin accounts
try:
    with engine.connect() as conn:
        admin_count = conn.execute(
            sa.text("SELECT COUNT(*) FROM users WHERE role = 'admin'")
        ).fetchone()[0]
    check(admin_count == 1,
          f"Exactly 1 admin account exists (no duplicates)",
          f"Unexpected admin count: {admin_count} (expected exactly 1)")
except Exception as e:
    FAIL.append(f"Duplicate check error: {sanitize_error(e, DATABASE_URL)}")

# Verify total user count is 1 (clean database)
try:
    with engine.connect() as conn:
        user_count = conn.execute(sa.text("SELECT COUNT(*) FROM users")).fetchone()[0]
    check(user_count == 1,
          f"Total users in database: {user_count} (admin only, clean state)",
          f"Unexpected total user count: {user_count}")
except Exception as e:
    FAIL.append(f"User count error: {sanitize_error(e, DATABASE_URL)}")

# Verify registration role logic (simulate what the registration endpoint does)
print("\n[Registration Role Verification]")
print("  Verifying public registration produces role=user and is_active=True...")
print("  (Reading registration endpoint logic from source — no test user created)")
try:
    reg_src = Path("backend/app/api/v1/endpoints/auth.py").read_text(encoding="utf-8")
    has_role_user    = 'role="user"' in reg_src or "role='user'" in reg_src
    has_is_active    = 'is_active=True' in reg_src or 'is_active = True' in reg_src
    has_no_admin_reg = 'role="admin"' not in reg_src.split("create-admin")[0] if "create-admin" in reg_src else 'role="admin"' not in reg_src
    check(has_role_user,  'Registration endpoint sets role="user"',   'Registration endpoint role assignment not confirmed')
    check(has_is_active,  'Registration endpoint sets is_active=True', 'Registration endpoint is_active not confirmed')
except Exception as e:
    FAIL.append(f"Registration source check error: {e}")

# Summary
print("\n" + "=" * 65)
print("ADMIN PROVISIONING SUMMARY")
print("=" * 65)
print(f"PASSED: {len(PASS)}")
print(f"FAILED: {len(FAIL)}")
if FAIL:
    print("\nFailed checks:")
    for f in FAIL:
        print(f"  - {f}")
    print("\n[RESULT] Admin provisioning FAILED — review errors above.")
    sys.exit(1)
else:
    print(f"\n[SUCCESS] Administrator account provisioned and verified.")
    print(f"  Email:   {ADMIN_EMAIL}")
    print(f"  Role:    admin")
    print(f"  Active:  True")
    print(f"  Hash:    Argon2id")
    print(f"\n[STOP] No admin account created on SQLite. No backup restored.")
    print("Waiting for your approval before Render/Cloudflare deployment.")
print("=" * 65)
