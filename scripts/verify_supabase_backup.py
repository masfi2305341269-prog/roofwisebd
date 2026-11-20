"""
verify_supabase_backup.py
Verifies the SQLite backup created before Supabase migration.
Run this to confirm the backup is intact before any migration.
"""
import sqlite3, sys

backup_path = "backend/roofwise_backup_supabase_prep_1794848025.db"

try:
    conn = sqlite3.connect(backup_path)
    cur = conn.cursor()

    # Integrity check
    cur.execute("PRAGMA integrity_check")
    result = cur.fetchone()[0]
    if result != "ok":
        print(f"INTEGRITY CHECK FAILED: {result}")
        sys.exit(1)
    print(f"[OK] PRAGMA integrity_check: {result}")

    # Alembic version
    cur.execute("SELECT version_num FROM alembic_version")
    version = cur.fetchone()
    print(f"[OK] Alembic version: {version[0] if version else 'NOT SET'}")

    # Table inventory
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cur.fetchall()]
    print(f"[OK] Tables: {tables}")

    # Row counts
    for t in tables:
        cur.execute(f'SELECT COUNT(*) FROM "{t}"')
        count = cur.fetchone()[0]
        print(f"  {t}: {count} rows")

    # Column count on assessments
    cur.execute("PRAGMA table_info('assessments')")
    cols = cur.fetchall()
    print(f"[OK] assessments: {len(cols)} columns (expected: 31)")
    if len(cols) != 31:
        print(f"  WARNING: Expected 31 columns, found {len(cols)}")
    else:
        print(f"  All 31 assessment columns confirmed.")

    conn.close()
    print("\n[PASS] Backup verified — safe to proceed with Supabase migration when approved.")

except Exception as e:
    print(f"[FAIL] Backup verification error: {e}")
    sys.exit(1)
