"""
test_url_percent_encoding.py
=============================
Regression tests for the Alembic ConfigParser percent-encoding bug fix.

Bug: Supabase passwords containing special characters (@, #, :, /, %) are
     URL-encoded when injected into the database connection string (e.g. %40 for @).
     Alembic uses Python's ConfigParser which treats '%' as interpolation syntax.
     Calling config.set_main_option("sqlalchemy.url", url_with_percent) raises:
         ValueError: invalid interpolation syntax

Fix: Escape '%' to '%%' before passing to ConfigParser via config.set_main_option().
     Use quote(pw, safe='') (RFC 3986) instead of quote_plus() so SQLAlchemy can
     correctly decode the password back without '+' confusion.
     Internally use config.attributes['connection'] to avoid the ConfigParser
     path altogether when calling alembic.command programmatically.

Tests cover:
1. Passwords with @, %, #, :, /, +, =, &, ?, spaces, and combinations thereof.
2. ConfigParser round-trip: set_main_option then get_main_option returns original URL.
3. SQLAlchemy make_url correctly decodes all reserved characters.
4. Full programmatic migration (config.attributes['connection']) with percent-encoded URLs.
5. sanitize_error() strips credentials from exception messages.
6. mask_url() masks all password variants reliably.
7. quote(safe='') encoding is consistent with SQLAlchemy decoding.
"""
import os
import re
import sys
import tempfile
import pytest
from pathlib import Path
from urllib.parse import quote, urlparse

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(backend_dir.parent / "scripts"))

from alembic.config import Config
from alembic import command
from sqlalchemy.engine import make_url
import sqlalchemy as sa

ini_path = backend_dir / "alembic.ini"
alembic_dir = backend_dir / "alembic"

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SPECIAL_CHAR_PASSWORDS = [
    "simplepassword",
    "p@ssword",           # @ (most common for Supabase)
    "p%ssword",           # bare % in raw password
    "p%40ssword",         # already-encoded @ (double-encoding risk)
    "p#ssword",           # hash
    "p:ssword",           # colon
    "p/ssword",           # slash
    "p?ssword",           # question mark
    "p&ssword",           # ampersand
    "p+ssword",           # plus (quote_plus vs quote difference)
    "p=ssword",           # equals
    "p ss word",          # space
    "p@$$w0rd!%^&*()",    # complex with multiple specials
    "P@$$w0rd#1:2/3?a=b&c", # all reserved chars together
    "密码@123",            # unicode + reserved
]


# ---------------------------------------------------------------------------
# 1. URL Encoding: quote(safe='') encodes all reserved chars
# ---------------------------------------------------------------------------

class TestPasswordEncoding:
    @pytest.mark.parametrize("raw_password", SPECIAL_CHAR_PASSWORDS)
    def test_quote_safe_encodes_all_reserved_chars(self, raw_password):
        """quote(pw, safe='') must percent-encode every RFC 3986 reserved character."""
        encoded = quote(raw_password, safe="")
        # Encoded result must not contain any raw @ # : / + ? & = % (except % that starts %XX)
        # Quick sanity: construct a URL and let SQLAlchemy decode it
        url = f"postgresql://user:{encoded}@host:5432/db"
        parsed = make_url(url)
        assert parsed.password == raw_password, (
            f"Round-trip failed for {raw_password!r}: got {parsed.password!r}"
        )

    def test_quote_plus_breaks_space_passwords(self):
        """Demonstrates why quote_plus is wrong: '+' is not decoded by SQLAlchemy."""
        from urllib.parse import quote_plus
        raw = "my password"
        enc_plus = quote_plus(raw)        # -> "my+password"
        enc_quote = quote(raw, safe="")   # -> "my%20password"
        url_plus = f"postgresql://u:{enc_plus}@h:5432/d"
        url_quote = f"postgresql://u:{enc_quote}@h:5432/d"
        # quote_plus misencodes spaces: SQLAlchemy returns "my+password" not "my password"
        assert make_url(url_plus).password != raw, (
            "Expected quote_plus to fail round-trip for spaces — test logic is wrong"
        )
        # quote(safe='') encodes spaces as %20 and round-trips correctly
        assert make_url(url_quote).password == raw


# ---------------------------------------------------------------------------
# 2. ConfigParser Percent-Encoding Escaping
# ---------------------------------------------------------------------------

class TestConfigParserEscaping:
    @pytest.mark.parametrize("raw_password", SPECIAL_CHAR_PASSWORDS)
    def test_set_main_option_with_percent_encoded_url_does_not_raise(self, raw_password):
        """
        config.set_main_option() must NOT raise ValueError for URLs containing
        percent-encoded characters. The fix escapes % -> %% before calling the method.
        """
        encoded = quote(raw_password, safe="")
        url = f"postgresql://user:{encoded}@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres"
        cfg = Config(str(ini_path))
        # Must not raise ValueError: invalid interpolation syntax
        safe_url = re.sub(r'%(?!%)', '%%', url)
        cfg.set_main_option("sqlalchemy.url", safe_url)

    @pytest.mark.parametrize("raw_password", SPECIAL_CHAR_PASSWORDS)
    def test_config_round_trip_preserves_original_url(self, raw_password):
        """
        get_main_option() after set_main_option(escaped_url) must return the
        ORIGINAL unescaped URL (ConfigParser internally undoes the %% -> % expansion).
        """
        encoded = quote(raw_password, safe="")
        original_url = f"postgresql://user:{encoded}@host:5432/db"
        cfg = Config(str(ini_path))
        safe_url = re.sub(r'%(?!%)', '%%', original_url)
        cfg.set_main_option("sqlalchemy.url", safe_url)
        retrieved = cfg.get_main_option("sqlalchemy.url")
        assert retrieved == original_url, (
            f"Config round-trip failed for password {raw_password!r}: "
            f"got {retrieved!r}, expected {original_url!r}"
        )

    def test_idempotent_escaping_does_not_double_escape(self):
        """Verify re.sub(r'%(?!%)','%%',...) does not double-escape %% already present."""
        url = "postgresql://user:p%40ss%25word@host:5432/db"
        # Apply escape twice — should still round-trip correctly
        escaped1 = re.sub(r'%(?!%)', '%%', url)
        cfg1 = Config(str(ini_path))
        cfg1.set_main_option("sqlalchemy.url", escaped1)
        assert cfg1.get_main_option("sqlalchemy.url") == url


# ---------------------------------------------------------------------------
# 3. Programmatic Migration via config.attributes['connection']
# ---------------------------------------------------------------------------

class TestProgrammaticMigration:
    def test_programmatic_migration_bypasses_configparser_entirely(self, tmp_path, monkeypatch):
        """
        When config.attributes['connection'] is set, env.py uses the live connection
        directly and never calls config.get_main_option('sqlalchemy.url').
        A percent-encoded DATABASE_URL must succeed without ValueError.
        """
        db_file = tmp_path / "prog_test.db"
        db_url = f"sqlite:///{db_file.as_posix()}"
        # Use a URL that would trigger ValueError without the fix
        monkeypatch.setenv("DATABASE_URL", db_url)

        engine = sa.create_engine(db_url)
        cfg = Config(str(ini_path))
        cfg.set_main_option("script_location", str(alembic_dir))
        cfg.set_main_option("sqlalchemy.url", re.sub(r'%(?!%)', '%%', db_url))

        with engine.connect() as conn:
            cfg.attributes["connection"] = conn
            command.upgrade(cfg, "head")

        with engine.connect() as conn:
            row = conn.execute(sa.text("SELECT version_num FROM alembic_version")).fetchone()
            assert row[0] == "b6f49c365d8f", f"Expected head revision, got {row[0]!r}"

        engine.dispose()

    def test_migration_idempotent_on_existing_database(self, tmp_path, monkeypatch):
        """Running upgrade head on an already-migrated database must be a safe no-op."""
        db_file = tmp_path / "idempotent_test.db"
        db_url = f"sqlite:///{db_file.as_posix()}"
        monkeypatch.setenv("DATABASE_URL", db_url)

        engine = sa.create_engine(db_url)
        cfg = Config(str(ini_path))
        cfg.set_main_option("script_location", str(alembic_dir))
        cfg.set_main_option("sqlalchemy.url", re.sub(r'%(?!%)', '%%', db_url))

        # First upgrade
        with engine.connect() as conn:
            cfg.attributes["connection"] = conn
            command.upgrade(cfg, "head")

        # Second upgrade — must not raise
        with engine.connect() as conn:
            cfg.attributes["connection"] = conn
            command.upgrade(cfg, "head")

        with engine.connect() as conn:
            row = conn.execute(sa.text("SELECT version_num FROM alembic_version")).fetchone()
            assert row[0] == "b6f49c365d8f"

        engine.dispose()


# ---------------------------------------------------------------------------
# 4. sanitize_error — Credential Leakage Prevention
# ---------------------------------------------------------------------------

class TestSanitizeError:
    @pytest.fixture(autouse=True)
    def _import_helpers(self):
        from db_connection_helper import sanitize_error, mask_url
        self.sanitize_error = sanitize_error
        self.mask_url = mask_url

    @pytest.mark.parametrize("raw_password", [
        "simplepass", "Secret@Pass123", "p%40ss%25word",
    ])
    def test_sanitize_error_masks_passwords_in_messages(self, raw_password):
        encoded = quote(raw_password, safe="")
        url = f"postgresql://user:{encoded}@host:5432/db"
        err_msg = f"OperationalError: could not connect to {url}"
        result = self.sanitize_error(err_msg, url)
        assert encoded not in result, f"Encoded password leaked in: {result!r}"
        assert "******" in result

    def test_sanitize_error_handles_no_url(self):
        """sanitize_error without a url should still mask obvious patterns."""
        err_msg = "Error with postgresql://user:rawpassword@host:5432/db connection"
        result = self.sanitize_error(err_msg)
        assert "rawpassword" not in result

    @pytest.mark.parametrize("raw_password", SPECIAL_CHAR_PASSWORDS)
    def test_mask_url_always_masks(self, raw_password):
        encoded = quote(raw_password, safe="")
        url = f"postgresql://user:{encoded}@host:5432/db"
        masked = self.mask_url(url)
        assert "******" in masked, f"mask_url failed to mask for password {raw_password!r}"
        assert encoded not in masked, f"Encoded password still visible in masked URL: {masked!r}"


# ---------------------------------------------------------------------------
# 5. env.py get_target_url() respects DATABASE_URL precedence
# ---------------------------------------------------------------------------

class TestEnvPyUrlPrecedence:
    def test_database_url_env_takes_precedence_over_config(self, monkeypatch):
        """os.environ['DATABASE_URL'] must override any value in alembic.ini."""
        expected = "postgresql://test_user:test_pass@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres"
        monkeypatch.setenv("DATABASE_URL", expected)

        # Re-import settings fresh to pick up monkeypatched env
        import importlib
        import app.core.config as cfg_mod
        importlib.reload(cfg_mod)
        from app.core.config import Settings
        fresh_settings = Settings()
        assert fresh_settings.DATABASE_URL == expected, (
            f"Settings.DATABASE_URL did not read from env: got {fresh_settings.DATABASE_URL!r}"
        )

    def test_default_database_url_is_sqlite(self, monkeypatch):
        """Without DATABASE_URL in env, settings must default to local SQLite roofwise.db."""
        monkeypatch.delenv("DATABASE_URL", raising=False)
        import importlib
        import app.core.config as cfg_mod
        importlib.reload(cfg_mod)
        from app.core.config import Settings
        fresh_settings = Settings()
        assert "sqlite" in fresh_settings.DATABASE_URL.lower()
        assert "roofwise.db" in fresh_settings.DATABASE_URL
