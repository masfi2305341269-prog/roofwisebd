"""
RoofwiseBD — Admin Account Supabase Auth Migration Script
=========================================================
Migrates the existing admin account from custom auth to Supabase Auth.

SAFE TO RUN: This script is idempotent and read-verify-write.
REQUIRES: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, DATABASE_URL env vars
NEVER run with production DATABASE_URL unless you know what you are doing.

Usage:
  python scripts/migrate_admin_to_supabase_auth.py --dry-run  # Inspect only
  python scripts/migrate_admin_to_supabase_auth.py            # Execute migration
"""
import os
import sys
import argparse
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

def main():
    parser = argparse.ArgumentParser(description="Migrate admin to Supabase Auth")
    parser.add_argument("--dry-run", action="store_true", help="Inspect without making changes")
    args = parser.parse_args()

    supabase_url = os.environ.get("SUPABASE_URL", "")
    service_role_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
    database_url = os.environ.get("DATABASE_URL", "")

    if not supabase_url or not service_role_key:
        print("ERROR: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
        sys.exit(1)

    print(f"Supabase URL: {supabase_url}")
    print(f"Database URL: {database_url[:40]}..." if database_url else "Database URL: (using default SQLite)")
    print(f"Dry run: {args.dry_run}")
    print()

    # Read admin from public.users
    from sqlalchemy import create_engine, text
    from app.core.config import settings

    db_url = database_url or str(settings.DATABASE_URL)
    engine = create_engine(db_url)

    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT id, email, hashed_password, full_name, role, is_active, auth_user_id "
            "FROM users WHERE email = 'admin@roofwisebd.com'"
        ))
        admin = result.mappings().first()

    if not admin:
        print("ERROR: admin@roofwisebd.com not found in public.users")
        sys.exit(1)

    print(f"Found admin: id={admin['id']}, email={admin['email']}, role={admin['role']}")
    print(f"  is_active: {admin['is_active']}")
    print(f"  auth_user_id: {admin['auth_user_id']} (None = not yet linked to Supabase)")
    print(f"  hashed_password: {'present' if admin['hashed_password'] else 'absent'}")
    print()

    if admin['auth_user_id']:
        print(f"Admin is already linked to Supabase auth_user_id={admin['auth_user_id']}")
        print("Nothing to do.")
        return

    if args.dry_run:
        print("[DRY RUN] Would create Supabase auth user for admin@roofwisebd.com with:")
        print(f"  password_hash: {admin['hashed_password'][:30]}... (Argon2id)")
        print("  email_confirm: True")
        print("  app_metadata.role: admin")
        print("[DRY RUN] Would UPDATE public.users SET auth_user_id=<uuid> WHERE email='admin@roofwisebd.com'")
        print("[DRY RUN] Complete. Run without --dry-run to execute.")
        return

    # Create Supabase auth user
    try:
        from supabase import create_client
    except ImportError:
        print("ERROR: supabase package not installed. Run: pip install supabase>=2.0.0")
        sys.exit(1)

    client = create_client(supabase_url, service_role_key)

    print("Creating Supabase auth user for admin@roofwisebd.com...")

    try:
        response = client.auth.admin.create_user({
            "email": "admin@roofwisebd.com",
            "password_hash": admin['hashed_password'],
            "email_confirm": True,
            "app_metadata": {"role": "admin"},
            "user_metadata": {"full_name": admin['full_name'] or "RoofwiseBD Administrator"}
        })
        auth_user = response.user
        auth_uid = str(auth_user.id)
        print(f"Created Supabase auth user: id={auth_uid}")
    except Exception as e:
        err_str = str(e)
        if "already registered" in err_str.lower() or "already exists" in err_str.lower():
            print(f"Auth user already exists. Fetching existing user...")
            # Try to get the existing user by email
            try:
                users_response = client.auth.admin.list_users()
                auth_uid = None
                for u in users_response:
                    if hasattr(u, 'email') and u.email == 'admin@roofwisebd.com':
                        auth_uid = str(u.id)
                        break
                if not auth_uid:
                    print("ERROR: Could not find existing Supabase auth user")
                    sys.exit(1)
                print(f"Found existing auth user: {auth_uid}")
            except Exception as e2:
                print(f"ERROR listing users: {e2}")
                sys.exit(1)
        else:
            print(f"ERROR creating auth user: {e}")
            sys.exit(1)

    # Link auth_user_id to public.users
    with engine.begin() as conn:
        conn.execute(text(
            "UPDATE users SET auth_user_id = :uid WHERE email = 'admin@roofwisebd.com' AND auth_user_id IS NULL"
        ), {"uid": auth_uid})

    print(f"Linked public.users.auth_user_id = {auth_uid} for admin@roofwisebd.com")
    print("Migration complete.")

if __name__ == "__main__":
    main()
