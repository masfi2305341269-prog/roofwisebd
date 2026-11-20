"""
RoofwiseBD — SQLite to PostgreSQL Production Data Migration Tool
================================================================
Transfers approved production records (users & assessments) from SQLite to PostgreSQL
with strict allowlisting, foreign key integrity preservation, sequence resetting,
and transactional safety.

SAFETY GUARANTEES:
1. Defaults to --dry-run. Requires explicit --execute to write.
2. Only transfers approved allowlisted accounts:
   - admin@roofwisebd.com
   - customer_test@roofwisebd.com (and associated assessments)
   - mashfihasan861@gmail.com
   - All valid guest assessments (user_id IS NULL)
3. Never transfers test accounts, expired sessions, legacy OTPs, or reset tokens.
4. Preserves:
   - Original users.id and assessments.id
   - Exact Argon2id password hashes for legacy/admin login
   - Foreign key integrity (assessments.user_id -> users.id)
   - Guest claim_token_hash
   - email_verified status and account role
5. Resets PostgreSQL identity sequences after explicit ID inserts.
6. Atomic transaction: rolls back completely on any error.
"""
import os
import sys
import argparse
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Tuple
from urllib.parse import urlparse

# Add backend and scripts to sys.path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
scripts_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

from db_connection_helper import get_supabase_url, mask_url, sanitize_error

DEFAULT_APPROVED_EMAILS = [
    "admin@roofwisebd.com",
    "customer_test@roofwisebd.com",
    "mashfihasan861@gmail.com",
]

def load_sqlite_records(sqlite_path: Path, approved_emails: List[str]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Extracts and filters records from local SQLite.
    Returns: (approved_users, excluded_users, target_assessments)
    """
    if not sqlite_path.exists():
        raise FileNotFoundError(f"SQLite database file not found at: {sqlite_path}")

    conn = sqlite3.connect(str(sqlite_path))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # 1. Extract all users
    user_rows = cur.execute("""
        SELECT id, email, auth_user_id, hashed_password, full_name, phone, address,
               role, is_active, email_verified, created_at, updated_at
        FROM users ORDER BY id
    """).fetchall()

    normalized_allowlist = set(e.strip().lower() for e in approved_emails)
    approved_users = []
    excluded_users = []

    for r in user_rows:
        u_dict = dict(r)
        u_dict["is_active"] = bool(u_dict["is_active"])
        u_dict["email_verified"] = bool(u_dict["email_verified"])
        if u_dict["email"].lower() in normalized_allowlist:
            approved_users.append(u_dict)
        else:
            excluded_users.append(u_dict)

    approved_user_ids = set(u["id"] for u in approved_users)

    # 2. Extract assessments
    # Include assessments belonging to approved users OR guest assessments (user_id IS NULL)
    assessment_rows = cur.execute("""
        SELECT id, created_at, user_id, claim_token_hash, division, district, area,
               latitude, longitude, monthly_units_kwh, billing_period_days, bill_amount_bdt,
               sanctioned_load_kw, consumer_category, total_area_sqft, usable_area_sqft,
               roof_type, shading_condition, orientation, tilt_degrees, bill_file_path,
               recommended_capacity_kwp, recommended_inverter_ac_kw, panel_count,
               daily_generation_kwh, monthly_generation_kwh, annual_generation_kwh,
               monthly_savings_bdt, estimated_payback_years, sreda_compliant, notes
        FROM assessments ORDER BY id
    """).fetchall()

    target_assessments = []
    excluded_assessments = []

    for r in assessment_rows:
        a_dict = dict(r)
        if a_dict["sreda_compliant"] is not None:
            a_dict["sreda_compliant"] = bool(a_dict["sreda_compliant"])
        uid = a_dict["user_id"]
        if uid is None or uid in approved_user_ids:
            target_assessments.append(a_dict)
        else:
            excluded_assessments.append(a_dict)

    conn.close()
    return approved_users, excluded_users, target_assessments


def run_migration(
    sqlite_path: Path,
    target_database_url: str,
    approved_emails: List[str],
    execute: bool = False,
    allow_sqlite_target: bool = False
) -> bool:
    print("=" * 75)
    print("ROOFWISEBD — SQLITE TO POSTGRESQL DATA MIGRATION")
    print(f"Mode: {'*** LIVE EXECUTION ***' if execute else 'DRY RUN (Read-Only Preview)'}")
    print("=" * 75)

    approved_users, excluded_users, target_assessments = load_sqlite_records(sqlite_path, approved_emails)

    print(f"\n[Source SQLite]: {sqlite_path}")
    print(f"  Total users in source:       {len(approved_users) + len(excluded_users)}")
    print(f"  Approved users to migrate:   {len(approved_users)}")
    print(f"  Excluded test users:         {len(excluded_users)}")
    print(f"  Assessments to migrate:      {len(target_assessments)}")

    print("\n--- APPROVED USERS TO MIGRATE ---")
    for u in approved_users:
        hash_preview = u["hashed_password"][:25] + "..." if u["hashed_password"] else "None"
        print(f"  [ID {u['id']:2d}] {u['email']:32s} | Role: {u['role']:5s} | Active: {u['is_active']} | Verified: {u['email_verified']} | Hash: {hash_preview}")

    print("\n--- EXCLUDED USERS (WILL NOT BE MIGRATED) ---")
    for u in excluded_users:
        print(f"  [ID {u['id']:2d}] {u['email']:32s} | Role: {u['role']:5s} | (Test/Dummy account)")

    print("\n--- ASSESSMENTS TO MIGRATE ---")
    for a in target_assessments:
        owner_desc = f"User ID {a['user_id']}" if a['user_id'] else "Guest (Claimable)"
        has_hash = bool(a['claim_token_hash'])
        print(f"  [ID {a['id']:2d}] Owner: {owner_desc:18s} | Loc: {a['division']}/{a['district']} | Cap: {a['recommended_capacity_kwp']} kWp | HasClaimHash: {has_hash}")

    if not execute:
        print("\n" + "=" * 75)
        print("[DRY RUN COMPLETE] Zero database writes performed.")
        print("To execute this transfer against target PostgreSQL, pass --execute.")
        print("=" * 75)
        return True

    # LIVE EXECUTION BLOCK
    if not target_database_url:
        print("\n[ABORT] No target database URL provided for execution.")
        return False

    if "sqlite" in target_database_url.lower() and not allow_sqlite_target:
        print("\n[ABORT] Target database URL points to SQLite. Target must be PostgreSQL (use --allow-sqlite-target only for unit tests).")
        return False

    import sqlalchemy as sa
    from sqlalchemy import text

    masked = mask_url(target_database_url)
    print(f"\n[CONNECTING] Target PostgreSQL: {masked}")

    db_url = target_database_url.replace("postgres://", "postgresql://", 1)
    engine = sa.create_engine(db_url, pool_pre_ping=True)

    try:
        with engine.begin() as conn:
            # 1. Verify schema tables exist
            inspector = sa.inspect(conn)
            schema = "public" if engine.dialect.name == "postgresql" else None
            existing_tables = set(inspector.get_table_names(schema=schema))
            for req in ["users", "assessments"]:
                if req not in existing_tables:
                    raise RuntimeError(f"Required table '{req}' does not exist in target database! Run migrations first.")

            # 2. Check for duplicate users
            existing_emails = set(r[0].lower() for r in conn.execute(text("SELECT email FROM users")).fetchall())
            duplicates = [u["email"] for u in approved_users if u["email"].lower() in existing_emails]
            if duplicates:
                raise RuntimeError(f"Duplicate user emails already exist in target database: {duplicates}")

            # 3. Check for duplicate assessment IDs
            existing_a_ids = set(r[0] for r in conn.execute(text("SELECT id FROM assessments")).fetchall())
            dup_a_ids = [a["id"] for a in target_assessments if a["id"] in existing_a_ids]
            if dup_a_ids:
                raise RuntimeError(f"Duplicate assessment IDs already exist in target database: {dup_a_ids}")

            # 4. Insert Users
            print(f"\n[Step 1/3] Inserting {len(approved_users)} approved users into public.users...")
            user_insert_stmt = text("""
                INSERT INTO users (
                    id, email, auth_user_id, hashed_password, full_name, phone, address,
                    role, is_active, email_verified, created_at, updated_at
                ) VALUES (
                    :id, :email, :auth_user_id, :hashed_password, :full_name, :phone, :address,
                    :role, :is_active, :email_verified, :created_at, :updated_at
                )
            """)
            for u in approved_users:
                conn.execute(user_insert_stmt, u)
            print(f"  Successfully inserted {len(approved_users)} user records.")

            # 5. Insert Assessments
            print(f"\n[Step 2/3] Inserting {len(target_assessments)} assessments into public.assessments...")
            assessment_insert_stmt = text("""
                INSERT INTO assessments (
                    id, created_at, user_id, claim_token_hash, division, district, area,
                    latitude, longitude, monthly_units_kwh, billing_period_days, bill_amount_bdt,
                    sanctioned_load_kw, consumer_category, total_area_sqft, usable_area_sqft,
                    roof_type, shading_condition, orientation, tilt_degrees, bill_file_path,
                    recommended_capacity_kwp, recommended_inverter_ac_kw, panel_count,
                    daily_generation_kwh, monthly_generation_kwh, annual_generation_kwh,
                    monthly_savings_bdt, estimated_payback_years, sreda_compliant, notes
                ) VALUES (
                    :id, :created_at, :user_id, :claim_token_hash, :division, :district, :area,
                    :latitude, :longitude, :monthly_units_kwh, :billing_period_days, :bill_amount_bdt,
                    :sanctioned_load_kw, :consumer_category, :total_area_sqft, :usable_area_sqft,
                    :roof_type, :shading_condition, :orientation, :tilt_degrees, :bill_file_path,
                    :recommended_capacity_kwp, :recommended_inverter_ac_kw, :panel_count,
                    :daily_generation_kwh, :monthly_generation_kwh, :annual_generation_kwh,
                    :monthly_savings_bdt, :estimated_payback_years, :sreda_compliant, :notes
                )
            """)
            for a in target_assessments:
                conn.execute(assessment_insert_stmt, a)
            print(f"  Successfully inserted {len(target_assessments)} assessment records.")

            # 6. Reset Sequences (PostgreSQL only)
            if engine.dialect.name == "postgresql":
                print("\n[Step 3/3] Resetting PostgreSQL identity sequences...")
                conn.execute(text("SELECT setval(pg_get_serial_sequence('users', 'id'), COALESCE((SELECT MAX(id) FROM users), 1));"))
                conn.execute(text("SELECT setval(pg_get_serial_sequence('assessments', 'id'), COALESCE((SELECT MAX(id) FROM assessments), 1));"))
                print("  Sequences reset to highest migrated IDs.")
            else:
                print(f"\n[Step 3/3] Skipping PostgreSQL identity sequence reset for dialect '{engine.dialect.name}'.")

            # 7. Verification inside transaction
            user_count = conn.execute(text("SELECT COUNT(*) FROM users")).scalar()
            assess_count = conn.execute(text("SELECT COUNT(*) FROM assessments")).scalar()
            print(f"\n[VERIFICATION] Final Target Record Counts:")
            print(f"  Users in database:       {user_count}")
            print(f"  Assessments in database: {assess_count}")

            # Verify admin account explicitly
            admin_row = conn.execute(text("SELECT id, email, role, email_verified, is_active FROM users WHERE role = 'admin'")).mappings().first()
            if not admin_row or admin_row["email"] != "admin@roofwisebd.com":
                raise RuntimeError("Post-migration integrity failure: Admin account not verified in target database!")
            print(f"  Admin account verified:  {admin_row['email']} (ID {admin_row['id']})")

        print("\n" + "=" * 75)
        print("[SUCCESS] TRANSACTION COMMITTED — MIGRATION FINISHED SAFELY")
        print("=" * 75)
        return True

    except Exception as e:
        err_msg = sanitize_error(e, target_database_url)
        print(f"\n[MIGRATION ERROR] Transaction aborted and rolled back: {err_msg}")
        return False


def main():
    parser = argparse.ArgumentParser(description="RoofwiseBD SQLite to PostgreSQL Data Migration Tool")
    parser.add_argument("--sqlite-db", type=Path, default=Path("F:/RoofWiseBD Web/backend/roofwise.db"),
                        help="Path to source SQLite database file")
    parser.add_argument("--target-url", type=str, default="",
                        help="Target PostgreSQL connection URL")
    parser.add_argument("--dry-run", action="store_true", default=False,
                        help="Simulate and preview data migration without writing")
    parser.add_argument("--execute", action="store_true", default=False,
                        help="Execute migration and write records into target PostgreSQL")
    parser.add_argument("--allow-sqlite-target", action="store_true", default=False,
                        help="Allow SQLite target for automated unit testing only")
    args = parser.parse_args()

    # Dry-run is the safe default unless --execute is explicitly specified
    execute_mode = args.execute and not args.dry_run

    target_url = args.target_url
    if execute_mode and not target_url:
        target_url = get_supabase_url()

    success = run_migration(
        sqlite_path=args.sqlite_db,
        target_database_url=target_url,
        approved_emails=DEFAULT_APPROVED_EMAILS,
        execute=execute_mode,
        allow_sqlite_target=args.allow_sqlite_target
    )

    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
