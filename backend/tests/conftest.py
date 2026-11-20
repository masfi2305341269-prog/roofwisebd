"""
RoofwiseBD — Global Pytest Configuration and Database Isolation Fixture
======================================================================
SAFETY GUARANTEE:
1. Automated tests must NEVER run against a production or live application database.
2. Every test session runs against an isolated, dedicated test SQLite database (test_roofwise_isolated.db).
3. If settings.DATABASE_URL or os.environ['DATABASE_URL'] points to a non-test database
   (such as PostgreSQL, Supabase, Render, or the main application roofwise.db), tests will
   refuse to run or drop any records.
4. All test data created during test runs is completely isolated from roofwise.db and any backups.
"""
import os
import sys
from pathlib import Path
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

# Ensure backend root directory is in sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Force test environment flags
os.environ["ENVIRONMENT"] = "test"
os.environ["ROOFWISE_ENV"] = "test"

# Dedicated, isolated test database path
TEST_DB_FILE = backend_dir / "test_roofwise_isolated.db"
TEST_DATABASE_URL = f"sqlite:///{TEST_DB_FILE.as_posix()}"

# Safety check: Detect forbidden production keywords in existing environment
_raw_env_url = os.environ.get("DATABASE_URL", "").lower()
_FORBIDDEN_KEYWORDS = ("supabase", "render", "postgres", "pooler", "aws", "rds", "prod")
for kw in _FORBIDDEN_KEYWORDS:
    if kw in _raw_env_url:
        raise RuntimeError(
            f"\n\n{'='*75}\n"
            f"FATAL SAFETY INTERLOCK TRIGGERED — Automated test execution aborted.\n"
            f"{'='*75}\n"
            f"DATABASE_URL in environment points to a non-test database containing '{kw}':\n"
            f"  {os.environ.get('DATABASE_URL')}\n"
            f"Automated tests are strictly forbidden from connecting to production/staging databases.\n"
            f"Unset DATABASE_URL or set it to an isolated test database before running pytest.\n"
            f"{'='*75}\n"
        )

# Explicitly set DATABASE_URL to the isolated test database
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

from app.core.config import settings
settings.DATABASE_URL = TEST_DATABASE_URL
settings.ENVIRONMENT = "test"

from app.database.database import Base, get_db
import app.database.database as db_module
from main import app

# Create isolated test engine
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

@event.listens_for(test_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

# Patch the global database module so any direct SessionLocal calls use the test engine
db_module.engine = test_engine
db_module.SessionLocal = TestingSessionLocal


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

# Override FastAPI get_db dependency
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """
    Session-wide fixture:
    1. Creates all schema tables on the isolated test database.
    2. Verifies that the test database is active and separate from roofwise.db.
    3. Yields for test execution.
    4. Teardown: Disposes connections and removes test_roofwise_isolated.db.
    """
    # Safety assertion
    assert "test" in str(test_engine.url).lower() or ":memory:" in str(test_engine.url).lower(), (
        f"CRITICAL SAFETY FAILURE: test_engine is pointing to non-test URL: {test_engine.url}"
    )
    assert "roofwise.db" not in str(test_engine.url).lower().split("test_")[0], (
        f"CRITICAL SAFETY FAILURE: test_engine must not point to main roofwise.db!"
    )

    # Create tables fresh on isolated test database
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    yield

    # Teardown
    test_engine.dispose()
    if TEST_DB_FILE.exists():
        try:
            TEST_DB_FILE.unlink()
        except Exception:
            pass


@pytest.fixture
def db_session():
    """Provides a transactional database session for tests requiring direct DB access."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
