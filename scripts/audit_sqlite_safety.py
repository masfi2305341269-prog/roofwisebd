"""
Audit all SQLite databases: SHA-256 checksums, exact sizes, modification times, integrity, row counts.
"""
import os
import hashlib
import sqlite3
import datetime
from pathlib import Path

db_dir = Path("backend")
dbs = [
    "roofwise.db",
    "roofwise_backup_1794839622.db",
    "roofwise_backup_remediation_1794842369.db",
    "roofwise_backup_phase2_1794844688.db",
    "roofwise_backup_verify_1794844955.db",
    "roofwise_backup_supabase_prep_1794848025.db",
]

print("=" * 80)
print("SQLITE FILES SAFETY & INTEGRITY AUDIT")
print("=" * 80)

for name in dbs:
    p = db_dir / name
    if not p.exists():
        print(f"{name}: NOT FOUND")
        continue
    size = p.stat().st_size
    mtime = datetime.datetime.fromtimestamp(p.stat().st_mtime)

    with open(p, "rb") as f:
        sha256 = hashlib.sha256(f.read()).hexdigest()

    conn = sqlite3.connect(str(p))
    cur = conn.cursor()
    cur.execute("PRAGMA integrity_check")
    integrity = cur.fetchone()[0]

    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cur.fetchall()]

    counts = {}
    for t in tables:
        cur.execute(f'SELECT COUNT(*) FROM "{t}"')
        counts[t] = cur.fetchone()[0]
    conn.close()

    print(f"File: {name}")
    print(f"  Size:         {size:,} bytes")
    print(f"  Modified:     {mtime.strftime('%Y-%m-%d %H:%M:%S')} local")
    print(f"  SHA-256:      {sha256}")
    print(f"  Integrity:    {integrity}")
    print(f"  Tables:       {tables}")
    print(f"  Counts:       {counts}")
    print("-" * 80)
