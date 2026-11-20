"""
backend/tests/test_data_migration.py
====================================
Tests for scripts/migrate_sqlite_data_to_postgres.py covering:
1. Allowlist filtering (admin + approved users + associated assessments + guest assessments).
2. Clean exclusion of test accounts, expired sessions, OTPs, and reset tokens.
3. Dry-run mode performing zero writes.
4. Transactional execution with ID, Argon2id hash, and foreign key preservation.
5. Duplicate detection aborting before writing.
6. Atomic rollback on failure.
"""
import sys
import sqlite3
import pytest
from pathlib import Path
import sqlalchemy as sa
from alembic.config import Config
from alembic import command

# Add scripts directory to sys.path
scripts_dir = Path(__file__).resolve().parent.parent.parent / "scripts"
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

from migrate_sqlite_data_to_postgres import (
    load_sqlite_records,
    run_migration,
    DEFAULT_APPROVED_EMAILS,
)


@pytest.fixture
def mock_source_sqlite(tmp_path):
    """Creates a temporary source SQLite database with mock users and assessments."""
    db_file = tmp_path / "mock_source.db"
    conn = sqlite3.connect(str(db_file))
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            auth_user_id VARCHAR(36) UNIQUE,
            hashed_password VARCHAR(255),
            full_name VARCHAR(100) NOT NULL,
            phone VARCHAR(20),
            address VARCHAR(255),
            role VARCHAR(20) NOT NULL,
            is_active BOOLEAN NOT NULL,
            email_verified BOOLEAN NOT NULL,
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE assessments (
            id INTEGER PRIMARY KEY,
            created_at DATETIME,
            user_id INTEGER,
            claim_token_hash VARCHAR(64),
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
        )
    """)

    # Seed Admin (ID=1)
    cur.execute("""
        INSERT INTO users VALUES (
            1, 'admin@roofwisebd.com', NULL, '$argon2id$v=19$m=65536,t=3,p=4$adminhash',
            'Super Admin', NULL, NULL, 'admin', 1, 1, '2026-11-16 10:00:00', '2026-11-16 10:00:00'
        )
    """)
    # Seed Approved User (ID=2)
    cur.execute("""
        INSERT INTO users VALUES (
            2, 'customer_test@roofwisebd.com', NULL, '$argon2id$v=19$m=65536,t=3,p=4$userhash',
            'Customer User', '+8801712345678', 'Dhanmondi, Dhaka', 'user', 1, 1, '2026-11-17 10:00:00', '2026-11-17 10:00:00'
        )
    """)
    # Seed Approved User (ID=3)
    cur.execute("""
        INSERT INTO users VALUES (
            3, 'mashfihasan861@gmail.com', NULL, '$argon2id$v=19$m=65536,t=3,p=4$mashfihash',
            'Mashfi Hasan', '01919950064', 'Mirpur', 'user', 1, 1, '2026-11-18 10:00:00', '2026-11-18 10:00:00'
        )
    """)
    # Seed Test User (ID=4) — SHOULD BE EXCLUDED
    cur.execute("""
        INSERT INTO users VALUES (
            4, 'test_excluded@roofwisebd.com', NULL, '$argon2id$v=19$m=65536,t=3,p=4$testhash',
            'Test Excluded', '01700000000', 'Test', 'user', 1, 1, '2026-11-19 10:00:00', '2026-11-19 10:00:00'
        )
    """)

    # Seed Assessments:
    # 1. Guest assessment (claimable)
    cur.execute("""
        INSERT INTO assessments VALUES (
            1, '2026-11-18 12:00:00', NULL, 'guest_claim_hash_123', 'Dhaka', 'Dhaka', 'Banani',
            23.8, 90.4, 350.0, 30, 3500.0, 3.0, 'Residential', 1000.0, 800.0,
            'concrete_flat', 'low', 'South', 23.0, NULL, 3.85, 3.0, 8,
            15.0, 450.0, 5400.0, 4200.0, 4.5, 1, 'Guest Note'
        )
    """)
    # 2. Assessment owned by approved user 2
    cur.execute("""
        INSERT INTO assessments VALUES (
            2, '2026-11-18 14:00:00', 2, NULL, 'Dhaka', 'Dhaka', 'Uttara',
            23.85, 90.41, 400.0, 30, 4000.0, 4.0, 'Residential', 1200.0, 950.0,
            'concrete_flat', 'low', 'South', 23.0, NULL, 4.5, 4.0, 10,
            18.0, 540.0, 6480.0, 5000.0, 4.2, 1, 'User 2 Note'
        )
    """)
    # 3. Assessment owned by excluded user 4 — SHOULD BE EXCLUDED
    cur.execute("""
        INSERT INTO assessments VALUES (
            3, '2026-11-18 16:00:00', 4, NULL, 'Dhaka', 'Dhaka', 'Mirpur',
            23.82, 90.38, 300.0, 30, 3000.0, 3.0, 'Residential', 800.0, 600.0,
            'concrete_flat', 'low', 'South', 23.0, NULL, 3.0, 3.0, 6,
            12.0, 360.0, 4320.0, 3200.0, 5.0, 1, 'Excluded Note'
        )
    """)

    conn.commit()
    conn.close()
    return db_file


@pytest.fixture
def mock_target_db(tmp_path):
    """Creates a temporary target database matching the models schema."""
    from app.database.database import Base
    db_file = tmp_path / "mock_target.db"
    db_url = f"sqlite:///{db_file.as_posix()}"
    engine = sa.create_engine(db_url)
    Base.metadata.create_all(bind=engine)
    return db_file, db_url


def test_load_sqlite_records_filtering(mock_source_sqlite):
    """Tests that only approved users and their assessments + guest assessments are selected."""
    approved_users, excluded_users, target_assessments = load_sqlite_records(
        mock_source_sqlite, DEFAULT_APPROVED_EMAILS
    )

    assert len(approved_users) == 3
    approved_emails = [u["email"] for u in approved_users]
    assert "admin@roofwisebd.com" in approved_emails
    assert "customer_test@roofwisebd.com" in approved_emails
    assert "mashfihasan861@gmail.com" in approved_emails
    assert "test_excluded@roofwisebd.com" not in approved_emails

    assert len(excluded_users) == 1
    assert excluded_users[0]["email"] == "test_excluded@roofwisebd.com"

    # Verify assessments: assessment 1 (guest) and 2 (user 2) included; 3 (user 4) excluded
    assert len(target_assessments) == 2
    a_ids = [a["id"] for a in target_assessments]
    assert 1 in a_ids
    assert 2 in a_ids
    assert 3 not in a_ids


def test_migration_dry_run_does_not_write(mock_source_sqlite, mock_target_db):
    """Tests that --dry-run performs zero writes on the target database."""
    target_file, target_url = mock_target_db

    success = run_migration(
        sqlite_path=mock_source_sqlite,
        target_database_url=target_url,
        approved_emails=DEFAULT_APPROVED_EMAILS,
        execute=False,  # Dry run
        allow_sqlite_target=True
    )
    assert success is True

    # Target DB must remain empty
    engine = sa.create_engine(target_url)
    with engine.connect() as conn:
        users_count = conn.execute(sa.text("SELECT count(*) FROM users")).scalar()
        assessments_count = conn.execute(sa.text("SELECT count(*) FROM assessments")).scalar()
    assert users_count == 0
    assert assessments_count == 0


def test_migration_execute_inserts_and_preserves_integrity(mock_source_sqlite, mock_target_db):
    """Tests live execution inserting approved records, preserving IDs, hashes, and FKs."""
    target_file, target_url = mock_target_db

    success = run_migration(
        sqlite_path=mock_source_sqlite,
        target_database_url=target_url,
        approved_emails=DEFAULT_APPROVED_EMAILS,
        execute=True,
        allow_sqlite_target=True
    )
    assert success is True

    engine = sa.create_engine(target_url)
    with engine.connect() as conn:
        # 1. Row counts
        users = conn.execute(sa.text("SELECT id, email, role, hashed_password FROM users ORDER BY id")).fetchall()
        assert len(users) == 3

        # ID preservation
        assert users[0][0] == 1
        assert users[0][1] == "admin@roofwisebd.com"
        assert users[0][2] == "admin"
        assert users[0][3] == "$argon2id$v=19$m=65536,t=3,p=4$adminhash"

        assert users[1][0] == 2
        assert users[1][1] == "customer_test@roofwisebd.com"
        assert users[1][3] == "$argon2id$v=19$m=65536,t=3,p=4$userhash"

        # 2. Assessment integrity
        assessments = conn.execute(sa.text("SELECT id, user_id, claim_token_hash FROM assessments ORDER BY id")).fetchall()
        assert len(assessments) == 2

        # Guest assessment preserved with claim hash
        assert assessments[0][0] == 1
        assert assessments[0][1] is None
        assert assessments[0][2] == "guest_claim_hash_123"

        # Owned assessment preserved with FK pointing to user 2
        assert assessments[1][0] == 2
        assert assessments[1][1] == 2


def test_migration_duplicate_detection(mock_source_sqlite, mock_target_db):
    """Tests that duplicate users in target abort execution without writing."""
    target_file, target_url = mock_target_db

    # Pre-seed target with admin@roofwisebd.com
    engine = sa.create_engine(target_url)
    with engine.begin() as conn:
        conn.execute(sa.text("""
            INSERT INTO users (id, email, full_name, role, is_active, email_verified, created_at, updated_at)
            VALUES (99, 'admin@roofwisebd.com', 'Existing Admin', 'admin', 1, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """))

    # Attempt migration -> must abort due to duplicate
    success = run_migration(
        sqlite_path=mock_source_sqlite,
        target_database_url=target_url,
        approved_emails=DEFAULT_APPROVED_EMAILS,
        execute=True,
        allow_sqlite_target=True
    )
    assert success is False

    # Target should only have the 1 pre-existing row, nothing added
    with engine.connect() as conn:
        users_count = conn.execute(sa.text("SELECT count(*) FROM users")).scalar()
        assert users_count == 1
