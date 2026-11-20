"""
test_migration_chain.py
=======================
Tests covering:
1. Complete migration chain from an entirely empty database (simulating fresh Supabase PostgreSQL).
2. Clean no-op execution on existing databases already at revision a5764b316a82.
3. Upgrading a pre-existing assessments database to a5764b316a82.
4. Offline SQL generation verifying PostgreSQL dialect and DDL completeness.
"""
import os
import sys
import sqlite3
import pytest
from pathlib import Path
from alembic.config import Config
from alembic import command
import sqlalchemy as sa

backend_dir = Path(__file__).resolve().parent.parent
ini_path = backend_dir / "alembic.ini"
alembic_dir = backend_dir / "alembic"


def get_alembic_config(db_url: str) -> Config:
    cfg = Config(str(ini_path))
    cfg.set_main_option("script_location", str(alembic_dir))
    cfg.set_main_option("sqlalchemy.url", db_url)
    return cfg


def test_migration_chain_from_empty_database(tmp_path, monkeypatch):
    """Verifies that an entirely empty database successfully runs the full migration chain to head."""
    db_file = tmp_path / "fresh_test.db"
    db_url = f"sqlite:///{db_file.as_posix()}"
    monkeypatch.setenv("DATABASE_URL", db_url)

    cfg = get_alembic_config(db_url)
    command.upgrade(cfg, "head")

    # Inspect created schema
    engine = sa.create_engine(db_url)
    inspector = sa.inspect(engine)
    tables = set(inspector.get_table_names())

    expected_tables = {"users", "assessments", "user_sessions", "password_reset_tokens", "alembic_version"}
    assert expected_tables.issubset(tables), f"Missing tables: {expected_tables - tables}"

    # Verify 31 columns on assessments
    cols = inspector.get_columns("assessments")
    assert len(cols) == 31, f"Expected 31 columns on assessments, got {len(cols)}"

    # Verify alembic_version
    with engine.connect() as conn:
        rev = conn.execute(sa.text("SELECT version_num FROM alembic_version")).scalar()
    assert rev == "b6f49c365d8f"


def test_existing_database_already_at_head_is_noop(tmp_path, monkeypatch):
    """Verifies that a database already at revision b6f49c365d8f safely no-ops without error."""
    db_file = tmp_path / "existing_head.db"
    db_url = f"sqlite:///{db_file.as_posix()}"
    monkeypatch.setenv("DATABASE_URL", db_url)

    # Create dummy database already marked at head
    conn = sqlite3.connect(str(db_file))
    conn.execute("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL, PRIMARY KEY (version_num));")
    conn.execute("INSERT INTO alembic_version VALUES ('b6f49c365d8f');")
    conn.commit()
    conn.close()

    cfg = get_alembic_config(db_url)
    # Must succeed cleanly without applying any new migrations
    command.upgrade(cfg, "head")

    conn = sqlite3.connect(str(db_file))
    cur = conn.cursor()
    cur.execute("SELECT version_num FROM alembic_version")
    rev = cur.fetchone()[0]
    conn.close()
    assert rev == "b6f49c365d8f"


def test_pre_existing_assessments_table_upgrades_cleanly(tmp_path, monkeypatch):
    """Verifies that a database having only the pre-existing assessments table upgrades cleanly."""
    db_file = tmp_path / "legacy_assessments.db"
    db_url = f"sqlite:///{db_file.as_posix()}"
    monkeypatch.setenv("DATABASE_URL", db_url)

    # Create original 29-column assessments table
    conn = sqlite3.connect(str(db_file))
    conn.execute("""
        CREATE TABLE assessments (
            id INTEGER PRIMARY KEY,
            created_at DATETIME,
            division VARCHAR(50) NOT NULL,
            district VARCHAR(50) NOT NULL,
            area VARCHAR(100),
            latitude FLOAT,
            longitude FLOAT,
            monthly_units_kwh FLOAT NOT NULL,
            billing_period_days INTEGER,
            bill_amount_bdt FLOAT,
            sanctioned_load_kw FLOAT,
            consumer_category VARCHAR(50),
            total_area_sqft FLOAT NOT NULL,
            usable_area_sqft FLOAT NOT NULL,
            roof_type VARCHAR(50),
            shading_condition VARCHAR(50),
            orientation VARCHAR(50),
            tilt_degrees FLOAT,
            bill_file_path VARCHAR(255),
            recommended_capacity_kwp FLOAT NOT NULL,
            recommended_inverter_ac_kw FLOAT NOT NULL,
            panel_count INTEGER NOT NULL,
            daily_generation_kwh FLOAT NOT NULL,
            monthly_generation_kwh FLOAT NOT NULL,
            annual_generation_kwh FLOAT NOT NULL,
            monthly_savings_bdt FLOAT NOT NULL,
            estimated_payback_years FLOAT NOT NULL,
            sreda_compliant BOOLEAN,
            notes TEXT
        );
    """)
    conn.commit()
    conn.close()

    cfg = get_alembic_config(db_url)
    command.upgrade(cfg, "head")

    engine = sa.create_engine(db_url)
    inspector = sa.inspect(engine)
    cols = inspector.get_columns("assessments")
    assert len(cols) == 31, f"Expected 31 columns, got {len(cols)}"

    with engine.connect() as conn_sa:
        rev = conn_sa.execute(sa.text("SELECT version_num FROM alembic_version")).scalar()
    assert rev == "b6f49c365d8f"


def test_postgresql_offline_sql_completeness():
    """Verifies that offline SQL generation for PostgreSQL contains all DDL statements."""
    import subprocess
    env = {
        **os.environ,
        "DATABASE_URL": "postgresql://test:test@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres",
        "PYTHONPATH": str(backend_dir)
    }
    cmd = [sys.executable, "-m", "alembic", "-c", str(ini_path), "upgrade", "head", "--sql"]
    res = subprocess.run(cmd, capture_output=True, text=True, env=env, cwd=str(backend_dir.parent))
    assert res.returncode == 0, f"SQL generation failed: {res.stderr}"

    full_output = res.stdout + res.stderr
    assert "Context impl PostgresqlImpl." in full_output
    assert "CREATE TABLE assessments (" in full_output
    assert "CREATE TABLE users (" in full_output
    assert "CREATE TABLE password_reset_tokens (" in full_output
    assert "CREATE TABLE user_sessions (" in full_output
    assert "ALTER TABLE assessments ADD COLUMN user_id INTEGER;" in full_output
    assert "ALTER TABLE assessments ADD COLUMN claim_token_hash VARCHAR(64);" in full_output
    assert "fk_assessments_users" in full_output
    assert "INSERT INTO alembic_version" in full_output
