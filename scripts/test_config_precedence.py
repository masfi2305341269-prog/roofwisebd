"""
test_config_precedence.py
=========================
Verifies that:
1. settings.DATABASE_URL correctly defaults to local SQLite.
2. settings.DATABASE_URL reflects os.environ['DATABASE_URL'] when set.
3. env.py's get_target_url() gives top priority to environment variable.
4. Batch mode is enabled for SQLite and disabled for PostgreSQL.
"""
import os
import sys
from pathlib import Path

# Add backend to sys.path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Test 1: Default SQLite behavior
if "DATABASE_URL" in os.environ:
    del os.environ["DATABASE_URL"]

from app.core.config import Settings
default_settings = Settings()
print(f"Test 1 (Default URL): {default_settings.DATABASE_URL}")
assert "sqlite" in default_settings.DATABASE_URL.lower(), "Default must be SQLite!"
assert "roofwise.db" in default_settings.DATABASE_URL, "Default must point to roofwise.db!"
print("  [PASS] Default DATABASE_URL is local SQLite roofwise.db")

# Test 2: Environment variable override
test_pg_url = "postgresql://test_user:test_pass@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres"
os.environ["DATABASE_URL"] = test_pg_url
overridden_settings = Settings()
print(f"Test 2 (Overridden URL): {overridden_settings.DATABASE_URL}")
assert overridden_settings.DATABASE_URL == test_pg_url, "DATABASE_URL did not take env override!"
print("  [PASS] os.environ['DATABASE_URL'] correctly overrides settings.DATABASE_URL")

# Test 3: env.py get_target_url precedence test
import importlib.util
spec = importlib.util.spec_from_file_location("alembic_custom_env", backend_dir / "alembic" / "env.py")
alembic_env = importlib.util.module_from_spec(spec)

# Mock context
import alembic
from unittest.mock import MagicMock
alembic.context = MagicMock()
alembic.context.config.config_file_name = None
alembic.context.config.get_main_option.return_value = None
alembic.context.is_offline_mode.return_value = True
spec.loader.exec_module(alembic_env)

resolved_url = alembic_env.get_target_url()
print(f"Test 3 (env.py get_target_url()): {resolved_url}")
assert resolved_url == test_pg_url, f"env.py did not resolve to env var! Got: {resolved_url}"
print("  [PASS] alembic env.py get_target_url() resolves directly to os.environ['DATABASE_URL']")

# Test 4: Batch mode toggle
print(f"Test 4 (Batch mode for PG): {alembic_env._use_batch}")
assert alembic_env._use_batch is False, "Batch mode should be FALSE on PostgreSQL!"
print("  [PASS] Batch mode correctly disabled for PostgreSQL")

# Test 5: Revert to SQLite and check batch mode
os.environ["DATABASE_URL"] = "sqlite:///backend/roofwise.db"
spec.loader.exec_module(alembic_env)
print(f"Test 5 (Batch mode for SQLite): {alembic_env._use_batch}")
assert alembic_env._use_batch is True, "Batch mode should be TRUE on SQLite!"
print("  [PASS] Batch mode correctly enabled for SQLite")

# Clean up env
del os.environ["DATABASE_URL"]
print("\n" + "=" * 65)
print("[ALL CONFIGURATION PRECEDENCE TESTS PASSED]")
print("=" * 65)
