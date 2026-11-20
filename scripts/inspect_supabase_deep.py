"""
inspect_supabase_deep.py
========================
Read-only deep inspection of Supabase PostgreSQL across all schemas.
SAFETY:
- Strictly read-only queries (SELECT only).
- Never modifies, creates, drops, or alters any database or table.
- Masks credentials in all outputs via sanitize_error() and mask_url().
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

from db_connection_helper import get_supabase_url, mask_url, sanitize_error

def deep_inspect(database_url: str = None):
    print("=" * 75)
    print("ROOFWISEBD — DEEP SUPABASE POSTGRESQL INSPECTION (READ-ONLY)")
    print("=" * 75)

    if not database_url:
        database_url = get_supabase_url()

    import sqlalchemy as sa
    from sqlalchemy import text

    masked = mask_url(database_url)
    print(f"[TARGET] {masked}")

    db_url = database_url.replace("postgres://", "postgresql://", 1)
    try:
        engine = sa.create_engine(db_url, pool_pre_ping=True, connect_args={"connect_timeout": 15})
    except Exception as e:
        print(f"[FAIL] Could not create engine: {sanitize_error(e, database_url)}")
        raise

    try:
        with engine.connect() as conn:
            # 1-4: Basic session diagnostics
            row = conn.execute(text(
                "SELECT current_database(), current_user, current_schema(), current_setting('search_path');"
            )).fetchone()
            curr_db, curr_user, curr_schema, search_path = row[0], row[1], row[2], row[3]

            print(f"1. current_database():             {curr_db}")
            print(f"2. current_user:                   {curr_user}")
            print(f"3. current_schema():               {curr_schema}")
            print(f"4. current_setting('search_path'): {search_path}")

            # 5. All schemas (system and non-system)
            schemas = [r[0] for r in conn.execute(text(
                "SELECT schema_name FROM information_schema.schemata ORDER BY schema_name;"
            )).fetchall()]
            non_system_schemas = [s for s in schemas if not s.startswith("pg_") and s != "information_schema"]

            print(f"\n5. All Schemas Found:              {schemas}")
            print(f"   Non-System Schemas:             {non_system_schemas}")

            # 6. All tables across all non-system schemas
            all_tables_query = text("""
                SELECT table_schema, table_name, table_type
                FROM information_schema.tables
                WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
                ORDER BY table_schema, table_name;
            """)
            tables_res = conn.execute(all_tables_query).fetchall()
            print(f"\n6. Tables across all non-system schemas (Total: {len(tables_res)}):")
            schema_table_map = {}
            for r in tables_res:
                s, t = r[0], r[1]
                schema_table_map.setdefault(s, []).append(t)

            for s in sorted(schema_table_map.keys()):
                print(f"   Schema '{s}': {schema_table_map[s]}")

            if not tables_res:
                print("   -> ZERO user or application tables found in ANY non-system schema.")

            # 7. Check if alembic_version exists anywhere
            alembic_search = text("""
                SELECT table_schema, table_name
                FROM information_schema.tables
                WHERE table_name = 'alembic_version';
            """)
            alembic_locations = conn.execute(alembic_search).fetchall()
            print(f"\n7. Does 'alembic_version' exist anywhere?")
            if alembic_locations:
                for al in alembic_locations:
                    print(f"   -> FOUND in schema: '{al[0]}'")
                    rev_row = conn.execute(text(f'SELECT version_num FROM "{al[0]}"."alembic_version"')).fetchone()
                    rev = rev_row[0] if rev_row else "empty"
                    print(f"8. Current Alembic Revision in '{al[0]}': {rev}")
            else:
                print("   -> 'alembic_version' table DOES NOT EXIST in ANY schema.")
                print("8. Current Alembic Revision: None (No migration has ever run on this database).")

            # Save to JSON
            report = {
                "current_database": curr_db,
                "current_user": curr_user,
                "current_schema": curr_schema,
                "search_path": search_path,
                "all_schemas": schemas,
                "non_system_schemas": non_system_schemas,
                "schema_table_map": schema_table_map,
                "alembic_version_locations": [list(x) for x in alembic_locations],
            }
            out_file = scripts_dir / "supabase_deep_inspection_report.json"
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2)
            print(f"\n[OK] Deep inspection report saved to: {out_file.name}")
    except Exception as e:
        print(f"[FAIL] Inspection error: {sanitize_error(e, database_url)}")
        raise

if __name__ == "__main__":
    deep_inspect()
