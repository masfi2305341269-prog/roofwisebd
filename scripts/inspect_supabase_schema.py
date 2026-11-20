"""
inspect_supabase_schema.py
==========================
Read-only inspection of the Supabase PostgreSQL database public schema.
Verifies whether any tables or alembic revisions were partially created.

SAFETY:
- Strictly read-only queries (SELECT only).
- Never modifies, creates, drops, or alters any database or table.
- Masks credentials in all outputs.
"""
import os
import sys
import json
from pathlib import Path

# Add backend and scripts to sys.path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
scripts_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

from db_connection_helper import get_supabase_url, mask_url

def inspect_schema():
    print("=" * 65)
    print("RoofwiseBD — Supabase PostgreSQL Schema Inspection (Read-Only)")
    print("=" * 65)

    database_url = get_supabase_url()
    masked = mask_url(database_url)
    print(f"\n[TARGET] Inspecting: {masked}")

    import sqlalchemy as sa
    from sqlalchemy import text

    db_url = database_url.replace("postgres://", "postgresql://", 1)
    engine = sa.create_engine(db_url, pool_pre_ping=True, connect_args={"connect_timeout": 15})
    inspector = sa.inspect(engine)

    with engine.connect() as conn:
        # 1. PostgreSQL Version
        pg_ver = conn.execute(text("SELECT version();")).scalar()
        print(f"[OK] PostgreSQL Version: {pg_ver[:60]}...")

        # 2. Public schema tables
        tables = inspector.get_table_names(schema="public")
        print(f"\n[INSPECTION] Public Schema Table Count: {len(tables)}")
        print(f"[INSPECTION] Tables Found: {tables if tables else 'None (Empty public schema)'}")

        # 3. Check for alembic_version specifically
        has_alembic = "alembic_version" in tables
        alembic_rev = None
        if has_alembic:
            row = conn.execute(text("SELECT version_num FROM alembic_version;")).fetchone()
            alembic_rev = row[0] if row else "Empty table"
            print(f"[INSPECTION] alembic_version table: PRESENT (current revision: {alembic_rev})")
        else:
            print("[INSPECTION] alembic_version table: NOT PRESENT")

        # 4. Check for any application tables
        app_tables = {"users", "assessments", "user_sessions", "password_reset_tokens"}
        found_app_tables = app_tables.intersection(set(tables))
        print(f"[INSPECTION] Application Tables Found: {sorted(found_app_tables) if found_app_tables else 'None'}")

        # 5. Check if any partial changes occurred
        partial_changes = bool(tables)
        print(f"\n[CONCLUSION] Partial Changes Detected: {partial_changes}")
        if not partial_changes:
            print("  -> Database is clean. No tables were created by the failed attempt.")
        else:
            print(f"  -> Existing tables detected: {tables}")

        # Save report
        report_file = scripts_dir / "supabase_schema_inspection.json"
        report_data = {
            "target": masked,
            "table_count": len(tables),
            "tables": tables,
            "alembic_version_table_present": has_alembic,
            "alembic_revision": alembic_rev,
            "application_tables_found": sorted(found_app_tables),
            "partial_changes_detected": partial_changes
        }
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2)
        print(f"\n[OK] Inspection report saved to: {report_file.name}")

if __name__ == "__main__":
    inspect_schema()
