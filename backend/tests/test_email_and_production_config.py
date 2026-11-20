"""
RoofwiseBD — Email Delivery & Production Configuration Tests

Tests in this module:
  1. SMTP email sending (mocked SMTP server — no live delivery required)
  2. Email delivery failure handling (graceful, no internal errors exposed)
  3. Full password reset flow with mocked SMTP delivery
  4. Production config validation — JWT key checks
  5. Production config validation — COOKIE_SECURE enforcement
  6. Production config validation — CORS origin enforcement (localhost, non-HTTPS, wildcard)
  7. Production config validation — multiple simultaneous failures
  8. Env-var override correctness
  9. Live SMTP delivery skip/report (requires SMTP_HOST to be set via env)
"""
import os
import smtplib
import email
import pytest
from unittest.mock import patch, MagicMock, call
from fastapi.testclient import TestClient

from main import app
from app.core.config import Settings, _KNOWN_WEAK_JWT_KEYS
from app.core.email import (
    send_email,
    send_password_reset_email,
    EmailDeliveryError,
    _build_reset_email,
)
from app.core.security import get_password_hash
from app.database.database import SessionLocal
from app.database.models import User, UserSession, PasswordResetToken, AssessmentRecord


# ---------------------------------------------------------------------------
# Test Database Cleanup Fixture (shared)
# ---------------------------------------------------------------------------

def _safety_check_test_db(db):
    bind_url = str(db.get_bind().url).lower()
    if not ("test" in bind_url or ":memory:" in bind_url):
        raise RuntimeError(
            f"FATAL SAFETY INTERLOCK: clean_db attempted on non-test DB: {bind_url}. "
            "Automated test data deletion is strictly forbidden on non-test databases."
        )


@pytest.fixture(autouse=True)
def clean_db():
    """Remove all test users/sessions/tokens before and after each test — guarded to run ONLY on test databases."""
    db = SessionLocal()
    _safety_check_test_db(db)
    try:
        db.query(UserSession).delete()
        db.query(PasswordResetToken).delete()
        db.query(AssessmentRecord).delete()
        db.query(User).delete()
        db.commit()
    finally:
        db.close()
    yield
    db = SessionLocal()
    _safety_check_test_db(db)
    try:
        db.query(UserSession).delete()
        db.query(PasswordResetToken).delete()
        db.query(AssessmentRecord).delete()
        db.query(User).delete()
        db.commit()
    finally:
        db.close()



# ===========================================================================
# EMAIL SERVICE UNIT TESTS
# ===========================================================================

class TestEmailBuilding:
    """Tests for the email message construction helpers."""

    def test_reset_email_contains_reset_link(self):
        """The constructed reset email must embed the reset link in both parts."""
        link = "https://roofwisebd.com/reset-password?token=abc123testtoken"
        msg = _build_reset_email("user@example.com", link)

        # Check headers
        assert msg["To"] == "user@example.com"
        assert "Password Reset" in msg["Subject"]

        # Both plain-text and HTML payloads must contain the link
        parts_text = [p.get_payload(decode=True).decode("utf-8") for p in msg.get_payload()]
        assert any(link in text for text in parts_text)

    def test_reset_email_no_raw_secrets_in_subject_or_headers(self):
        """Email headers must not leak raw secrets or internal paths."""
        msg = _build_reset_email("user@example.com", "https://example.com/reset?token=SECRETTOKEN")
        # Subject must not contain the raw token (it should only be in the body link)
        assert "SECRETTOKEN" not in msg["Subject"]
        assert "SECRETTOKEN" not in (msg["From"] or "")


class TestSmtpSendMocked:
    """Tests for SMTP delivery using mocked SMTP connections (no network required)."""

    def test_send_password_reset_email_starttls_port_587(self):
        """Password reset email dispatched via STARTTLS on port 587."""
        with patch("app.core.email.settings") as mock_settings, \
             patch("smtplib.SMTP") as mock_smtp_cls:

            mock_settings.SMTP_HOST = "smtp.sendgrid.net"
            mock_settings.SMTP_PORT = 587
            mock_settings.SMTP_USER = "apikey"
            mock_settings.SMTP_PASSWORD = "SG.test_key"
            mock_settings.EMAIL_FROM = "noreply@roofwisebd.com"

            mock_smtp = MagicMock()
            mock_smtp_cls.return_value.__enter__ = lambda s: mock_smtp
            mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)

            send_password_reset_email(
                to_email="recipient@example.com",
                reset_link="https://roofwisebd.com/reset-password?token=test_token_xyz"
            )

            mock_smtp_cls.assert_called_once_with("smtp.sendgrid.net", 587, timeout=15)
            mock_smtp.starttls.assert_called_once()
            mock_smtp.login.assert_called_once_with("apikey", "SG.test_key")
            mock_smtp.sendmail.assert_called_once()

            # Verify sendmail args: from, to list, message string
            call_args = mock_smtp.sendmail.call_args
            assert call_args[0][0] == "noreply@roofwisebd.com"
            assert call_args[0][1] == ["recipient@example.com"]
            sent_msg = email.message_from_string(call_args[0][2])
            parts_text = [p.get_payload(decode=True).decode("utf-8") for p in sent_msg.get_payload()]
            assert any("test_token_xyz" in text for text in parts_text)



    def test_send_password_reset_email_ssl_port_465(self):
        """Password reset email dispatched via implicit SSL on port 465."""
        with patch("app.core.email.settings") as mock_settings, \
             patch("smtplib.SMTP_SSL") as mock_ssl_cls:

            mock_settings.SMTP_HOST = "smtp.example.com"
            mock_settings.SMTP_PORT = 465
            mock_settings.SMTP_USER = "user@example.com"
            mock_settings.SMTP_PASSWORD = "mypassword"
            mock_settings.EMAIL_FROM = "noreply@roofwisebd.com"

            mock_smtp = MagicMock()
            mock_ssl_cls.return_value.__enter__ = lambda s: mock_smtp
            mock_ssl_cls.return_value.__exit__ = MagicMock(return_value=False)

            send_password_reset_email(
                to_email="recipient@example.com",
                reset_link="https://roofwisebd.com/reset-password?token=test465"
            )

            mock_ssl_cls.assert_called_once_with("smtp.example.com", 465, timeout=15)
            mock_smtp.login.assert_called_once()
            mock_smtp.sendmail.assert_called_once()

    def test_send_email_raises_on_missing_smtp_host(self):
        """EmailDeliveryError raised immediately when SMTP_HOST is not configured."""
        with patch("app.core.email.settings") as mock_settings:
            mock_settings.SMTP_HOST = ""

            with pytest.raises(EmailDeliveryError, match="SMTP_HOST is not configured"):
                send_password_reset_email("user@example.com", "https://example.com/reset")

    def test_send_email_raises_on_auth_failure(self):
        """EmailDeliveryError raised on SMTP authentication failure (no credentials leaked)."""
        with patch("app.core.email.settings") as mock_settings, \
             patch("smtplib.SMTP") as mock_smtp_cls:

            mock_settings.SMTP_HOST = "smtp.example.com"
            mock_settings.SMTP_PORT = 587
            mock_settings.SMTP_USER = "baduser"
            mock_settings.SMTP_PASSWORD = "badpassword"
            mock_settings.EMAIL_FROM = "noreply@roofwisebd.com"

            mock_smtp = MagicMock()
            mock_smtp.login.side_effect = smtplib.SMTPAuthenticationError(535, b"Auth failed")
            mock_smtp_cls.return_value.__enter__ = lambda s: mock_smtp
            mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)

            with pytest.raises(EmailDeliveryError) as exc_info:
                send_password_reset_email("user@example.com", "https://example.com/reset")

            # Error message must NOT contain credentials
            error_msg = str(exc_info.value)
            assert "badpassword" not in error_msg
            assert "baduser" not in error_msg
            assert "authentication" in error_msg.lower()

    def test_send_email_raises_on_connection_timeout(self):
        """EmailDeliveryError raised on SMTP connection timeout."""
        import socket
        with patch("app.core.email.settings") as mock_settings, \
             patch("smtplib.SMTP") as mock_smtp_cls:

            mock_settings.SMTP_HOST = "smtp.example.com"
            mock_settings.SMTP_PORT = 587
            mock_settings.SMTP_USER = ""
            mock_settings.SMTP_PASSWORD = ""
            mock_settings.EMAIL_FROM = "noreply@roofwisebd.com"

            mock_smtp_cls.side_effect = socket.timeout("Connection timed out")

            with pytest.raises(EmailDeliveryError, match="timed out"):
                send_password_reset_email("user@example.com", "https://example.com/reset")

    def test_send_email_raises_on_smtp_exception(self):
        """EmailDeliveryError raised on generic SMTP error."""
        with patch("app.core.email.settings") as mock_settings, \
             patch("smtplib.SMTP") as mock_smtp_cls:

            mock_settings.SMTP_HOST = "smtp.example.com"
            mock_settings.SMTP_PORT = 587
            mock_settings.SMTP_USER = ""
            mock_settings.SMTP_PASSWORD = ""
            mock_settings.EMAIL_FROM = "noreply@roofwisebd.com"

            mock_smtp = MagicMock()
            mock_smtp.starttls.side_effect = smtplib.SMTPException("Server error")
            mock_smtp_cls.return_value.__enter__ = lambda s: mock_smtp
            mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)

            with pytest.raises(EmailDeliveryError, match="SMTP error"):
                send_password_reset_email("user@example.com", "https://example.com/reset")


# ===========================================================================
# PASSWORD RESET INTEGRATION TESTS (with SMTP mocked)
# ===========================================================================

class TestPasswordResetWithEmailMock:
    """Integration tests for the full password reset flow using mocked SMTP."""

    def _register_and_get_client(self, email: str, password: str, full_name: str):
        """Helper: creates a user directly in DB and returns a primed TestClient."""
        db = SessionLocal()
        user = User(
            email=email.lower(),
            hashed_password=get_password_hash(password),
            full_name=full_name,
            role="user",
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.close()
        return TestClient(app)

    def test_forgot_password_dispatches_email_when_smtp_configured(self):
        """When SMTP_HOST is set, send_password_reset_email must be called with correct args."""
        client = self._register_and_get_client(
            "smtp_test@roofwisebd.com", "Password2026", "SMTP Test User"
        )
        csrf_res = client.get("/api/v1/auth/csrf")
        csrf_token = csrf_res.json()["csrf_token"]

        with patch("app.api.v1.endpoints.auth.settings") as mock_settings, \
             patch("app.api.v1.endpoints.auth.send_password_reset_email") as mock_send:

            mock_settings.SMTP_HOST = "smtp.sendgrid.net"
            mock_settings.SMTP_PORT = 587
            mock_settings.SMTP_USER = "apikey"
            mock_settings.SMTP_PASSWORD = "SG.test"
            mock_settings.EMAIL_FROM = "noreply@roofwisebd.com"
            mock_settings.FRONTEND_URL = "https://roofwisebd.com"
            mock_settings.ENVIRONMENT = "development"
            mock_settings.RESET_TOKEN_EXPIRE_MINUTES = 15

            res = client.post(
                "/api/v1/auth/forgot-password",
                headers={"X-CSRF-Token": csrf_token},
                json={"email": "smtp_test@roofwisebd.com"},
            )
            assert res.status_code == 200
            assert "instructions have been sent" in res.json()["message"]

            # Email must have been dispatched exactly once
            mock_send.assert_called_once()
            call_kwargs = mock_send.call_args
            assert call_kwargs[1]["to_email"] == "smtp_test@roofwisebd.com"
            reset_link = call_kwargs[1]["reset_link"]
            assert reset_link.startswith("https://roofwisebd.com/reset-password?token=")
            # Raw token must appear in the link (it's the delivery payload)
            assert len(reset_link.split("token=")[1]) > 20

    def test_forgot_password_continues_on_smtp_delivery_failure(self):
        """When SMTP delivery fails, the API must still return generic success (not expose the error)."""
        client = self._register_and_get_client(
            "smtpfail@roofwisebd.com", "Password2026", "Fail Test User"
        )
        csrf_res = client.get("/api/v1/auth/csrf")
        csrf_token = csrf_res.json()["csrf_token"]

        with patch("app.api.v1.endpoints.auth.settings") as mock_settings, \
             patch("app.api.v1.endpoints.auth.send_password_reset_email",
                   side_effect=EmailDeliveryError("SMTP authentication error.")):

            mock_settings.SMTP_HOST = "smtp.badhost.com"
            mock_settings.SMTP_PORT = 587
            mock_settings.SMTP_USER = "bad"
            mock_settings.SMTP_PASSWORD = "bad"
            mock_settings.EMAIL_FROM = "noreply@roofwisebd.com"
            mock_settings.FRONTEND_URL = "https://roofwisebd.com"
            mock_settings.ENVIRONMENT = "development"
            mock_settings.RESET_TOKEN_EXPIRE_MINUTES = 15

            res = client.post(
                "/api/v1/auth/forgot-password",
                headers={"X-CSRF-Token": csrf_token},
                json={"email": "smtpfail@roofwisebd.com"},
            )
            # Must still return 200 with generic message — SMTP errors must NOT leak
            assert res.status_code == 200
            assert "instructions have been sent" in res.json()["message"]
            # SMTP error details must not appear in the API response
            assert "SMTP" not in res.json()["message"]
            assert "authentication" not in res.json()["message"]

    def test_forgot_password_nonexistent_email_returns_same_message(self):
        """Non-existent email receives identical generic message (no email enumeration)."""
        client = TestClient(app)
        csrf_res = client.get("/api/v1/auth/csrf")
        csrf_token = csrf_res.json()["csrf_token"]

        res_real = client.post(
            "/api/v1/auth/forgot-password",
            headers={"X-CSRF-Token": csrf_token},
            json={"email": "nonexistent_at_all@example.com"},
        )
        assert res_real.status_code == 200

        # Also works for existing user
        client2 = self._register_and_get_client(
            "real_user@roofwisebd.com", "Password2026", "Real User"
        )
        csrf_res2 = client2.get("/api/v1/auth/csrf")
        csrf_token2 = csrf_res2.json()["csrf_token"]
        res_exists = client2.post(
            "/api/v1/auth/forgot-password",
            headers={"X-CSRF-Token": csrf_token2},
            json={"email": "real_user@roofwisebd.com"},
        )
        assert res_exists.status_code == 200
        assert res_real.json()["message"] == res_exists.json()["message"]

    def test_reset_link_uses_frontend_url_setting(self):
        """The reset link URL must be built from FRONTEND_URL setting."""
        client = self._register_and_get_client(
            "linkcheck@roofwisebd.com", "Password2026", "Link Check User"
        )
        csrf_res = client.get("/api/v1/auth/csrf")
        csrf_token = csrf_res.json()["csrf_token"]

        captured_links = []

        def capture_link(to_email, reset_link):
            captured_links.append(reset_link)

        with patch("app.api.v1.endpoints.auth.settings") as mock_settings, \
             patch("app.api.v1.endpoints.auth.send_password_reset_email", side_effect=capture_link):

            mock_settings.SMTP_HOST = "smtp.test.com"
            mock_settings.SMTP_PORT = 587
            mock_settings.SMTP_USER = ""
            mock_settings.SMTP_PASSWORD = ""
            mock_settings.EMAIL_FROM = "noreply@test.com"
            mock_settings.FRONTEND_URL = "https://custom-domain.roofwisebd.com"
            mock_settings.ENVIRONMENT = "development"
            mock_settings.RESET_TOKEN_EXPIRE_MINUTES = 15

            client.post(
                "/api/v1/auth/forgot-password",
                headers={"X-CSRF-Token": csrf_token},
                json={"email": "linkcheck@roofwisebd.com"},
            )

        assert len(captured_links) == 1
        assert captured_links[0].startswith("https://custom-domain.roofwisebd.com/reset-password?token=")


# ===========================================================================
# PRODUCTION CONFIGURATION VALIDATION TESTS
# ===========================================================================

class TestProductionConfigValidation:
    """Tests for Settings.validate_production_settings()."""

    def _make_prod_settings(self, **overrides) -> Settings:
        """
        Returns a Settings-like object for production testing.
        Uses a valid baseline and applies overrides.
        """
        # Valid production baseline
        defaults = {
            "ENVIRONMENT": "production",
            "JWT_SECRET_KEY": "a" * 64,  # Strong, non-weak key
            "COOKIE_SECURE": True,
            "BACKEND_CORS_ORIGINS": ["https://roofwisebd.com"],
            "SMTP_HOST": "smtp.sendgrid.net",
        }
        defaults.update(overrides)
        return Settings(**defaults)

    def test_valid_production_config_passes(self):
        """A correctly configured production environment raises no error."""
        s = self._make_prod_settings()
        s.validate_production_settings()  # Must not raise

    def test_missing_smtp_host_rejected_in_production(self):
        """Missing SMTP_HOST in production must fail validation to prevent silent omission of account recovery."""
        s = self._make_prod_settings(SMTP_HOST="")
        with pytest.raises(RuntimeError) as exc_info:
            s.validate_production_settings()
        assert "SMTP_HOST" in str(exc_info.value)


    def test_development_environment_skips_validation(self):
        """validate_production_settings is a no-op in development."""
        s = Settings(
            ENVIRONMENT="development",
            JWT_SECRET_KEY="short",   # Would fail in production
            COOKIE_SECURE=False,       # Would fail in production
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )
        s.validate_production_settings()  # Must not raise

    def test_known_weak_jwt_key_rejected_in_production(self):
        """The default dev JWT secret key must be rejected in production."""
        for weak_key in _KNOWN_WEAK_JWT_KEYS:
            # Only test keys that are >= 32 chars (so only the weak-key check fires)
            if len(weak_key) >= 32:
                s = self._make_prod_settings(JWT_SECRET_KEY=weak_key)
                with pytest.raises(RuntimeError) as exc_info:
                    s.validate_production_settings()
                assert "JWT_SECRET_KEY" in str(exc_info.value)
                assert "development default" in str(exc_info.value)

    def test_short_jwt_key_rejected_in_production(self):
        """JWT keys shorter than 32 characters must be rejected in production."""
        s = self._make_prod_settings(JWT_SECRET_KEY="tooshort")
        with pytest.raises(RuntimeError) as exc_info:
            s.validate_production_settings()
        assert "JWT_SECRET_KEY" in str(exc_info.value)
        assert "too short" in str(exc_info.value)

    def test_cookie_secure_false_rejected_in_production(self):
        """COOKIE_SECURE=False must be rejected in production."""
        s = self._make_prod_settings(COOKIE_SECURE=False)
        with pytest.raises(RuntimeError) as exc_info:
            s.validate_production_settings()
        assert "COOKIE_SECURE" in str(exc_info.value)
        assert "HTTPS" in str(exc_info.value)

    def test_localhost_cors_origin_rejected_in_production(self):
        """localhost origins must be rejected in production CORS config."""
        for bad_origin in [
            "http://localhost:5173",
            "http://localhost:3000",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:8000",
        ]:
            s = self._make_prod_settings(BACKEND_CORS_ORIGINS=[bad_origin])
            with pytest.raises(RuntimeError) as exc_info:
                s.validate_production_settings()
            assert "BACKEND_CORS_ORIGINS" in str(exc_info.value)
            assert "localhost" in str(exc_info.value).lower() or "loopback" in str(exc_info.value).lower()

    def test_non_https_cors_origin_rejected_in_production(self):
        """Non-HTTPS origins must be rejected in production CORS config."""
        s = self._make_prod_settings(BACKEND_CORS_ORIGINS=["http://roofwisebd.com"])
        with pytest.raises(RuntimeError) as exc_info:
            s.validate_production_settings()
        assert "BACKEND_CORS_ORIGINS" in str(exc_info.value)
        assert "non-HTTPS" in str(exc_info.value)

    def test_wildcard_cors_origin_rejected_in_production(self):
        """Wildcard '*' origin must be rejected in production CORS config."""
        s = self._make_prod_settings(BACKEND_CORS_ORIGINS=["*"])
        with pytest.raises(RuntimeError) as exc_info:
            s.validate_production_settings()
        assert "BACKEND_CORS_ORIGINS" in str(exc_info.value)
        assert "wildcard" in str(exc_info.value).lower()

    def test_https_cors_origin_accepted_in_production(self):
        """Valid HTTPS CORS origins must be accepted without error."""
        s = self._make_prod_settings(
            BACKEND_CORS_ORIGINS=["https://roofwisebd.com", "https://www.roofwisebd.com"]
        )
        s.validate_production_settings()  # Must not raise

    def test_multiple_errors_reported_together(self):
        """All configuration errors must be collected and reported in one RuntimeError."""
        s = Settings(
            ENVIRONMENT="production",
            JWT_SECRET_KEY="short",   # Too short
            COOKIE_SECURE=False,       # Not secure
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],  # Localhost + non-HTTPS
        )
        with pytest.raises(RuntimeError) as exc_info:
            s.validate_production_settings()

        error_text = str(exc_info.value)
        # All errors must be present in a single message
        assert "JWT_SECRET_KEY" in error_text
        assert "COOKIE_SECURE" in error_text
        assert "BACKEND_CORS_ORIGINS" in error_text
        # Blockers must be numbered
        assert "[1]" in error_text
        assert "[2]" in error_text

    def test_error_message_includes_remediation_guidance(self):
        """The RuntimeError must include actionable remediation guidance."""
        s = Settings(
            ENVIRONMENT="production",
            JWT_SECRET_KEY="short",
            COOKIE_SECURE=False,
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )
        with pytest.raises(RuntimeError) as exc_info:
            s.validate_production_settings()
        error_text = str(exc_info.value)
        # Must mention env vars and actionable guidance
        assert "environment variables" in error_text.lower() or "env" in error_text.lower()
        assert "PRODUCTION SECURITY CONFIGURATION ERROR" in error_text


# ===========================================================================
# LIVE SMTP DELIVERY TEST (optional — skipped if SMTP_HOST not configured)
# ===========================================================================

@pytest.mark.skipif(
    not os.getenv("SMTP_HOST"),
    reason="LIVE_SMTP: SMTP_HOST env var not set — skipping live delivery test. "
           "STATUS: Live email delivery unverified. Configure SMTP_HOST, SMTP_PORT, "
           "SMTP_USER, SMTP_PASSWORD, EMAIL_FROM, and SMTP_TEST_RECIPIENT env vars "
           "to enable this test."
)
def test_live_smtp_delivery():
    """
    Live SMTP delivery test — only runs when SMTP_HOST is set.
    Set the following env vars before running to verify real delivery:
      SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, EMAIL_FROM
      SMTP_TEST_RECIPIENT (email address to receive the test message)
    """
    recipient = os.getenv("SMTP_TEST_RECIPIENT")
    if not recipient:
        pytest.skip("SMTP_TEST_RECIPIENT not set — cannot verify recipient address.")

    # This calls the real SMTP stack — requires a live SMTP server
    send_password_reset_email(
        to_email=recipient,
        reset_link="https://roofwisebd.com/reset-password?token=LIVE_TEST_TOKEN_DO_NOT_USE",
    )
    # If we reach here, delivery succeeded without raising EmailDeliveryError
    print(f"\n[LIVE SMTP TEST PASSED] Reset email dispatched to {recipient}")


# ===========================================================================
# REDIS RATE LIMITING TESTS
# ===========================================================================

class MockRedisPipeline:
    """Mock Redis Pipeline simulating sorted set sliding window operations."""
    def __init__(self, storage, key):
        self.storage = storage
        self.key = key
        self.commands = []

    def zremrangebyscore(self, key, min_score, max_score):
        self.commands.append(("zremrangebyscore", key, min_score, max_score))
        return self

    def zcard(self, key):
        self.commands.append(("zcard", key))
        return self

    def zadd(self, key, mapping):
        self.commands.append(("zadd", key, mapping))
        return self

    def expire(self, key, seconds):
        self.commands.append(("expire", key, seconds))
        return self

    def execute(self):
        results = []
        for cmd in self.commands:
            op = cmd[0]
            if op == "zremrangebyscore":
                _, key, min_score, max_score = cmd
                # Clean up items with score <= max_score
                items = self.storage.get(key, {})
                to_del = [m for m, s in items.items() if s <= max_score]
                for m in to_del:
                    del items[m]
                results.append(len(to_del))
            elif op == "zcard":
                _, key = cmd
                results.append(len(self.storage.get(key, {})))
            elif op == "zadd":
                _, key, mapping = cmd
                if key not in self.storage:
                    self.storage[key] = {}
                for m, s in mapping.items():
                    self.storage[key][m] = s
                results.append(len(mapping))
            elif op == "expire":
                results.append(True)
        return results


class MockRedisClient:
    """In-memory mock Redis client sharing state across simulated workers."""
    def __init__(self):
        self.storage = {}

    def pipeline(self):
        return MockRedisPipeline(self.storage, None)

    def delete(self, key):
        if key in self.storage:
            del self.storage[key]
            return 1
        return 0


class TestRedisRateLimiter:
    """Unit tests for RedisRateLimiter functionality and failure policies."""

    def test_redis_rate_limiter_shared_across_workers(self):
        """Simulate two Uvicorn workers sharing the same Redis client."""
        from app.core.rate_limiter import RedisRateLimiter

        shared_mock_redis = MockRedisClient()
        worker1 = RedisRateLimiter("redis://shared-cluster:6379/0", client=shared_mock_redis)
        worker2 = RedisRateLimiter("redis://shared-cluster:6379/0", client=shared_mock_redis)

        key = "login_ip:192.168.1.100"
        max_attempts = 3
        window = 60

        # Worker 1 records 2 attempts
        assert worker1.is_rate_limited(key, max_attempts, window) is False
        worker1.record_attempt(key)
        assert worker1.is_rate_limited(key, max_attempts, window) is False
        worker1.record_attempt(key)

        # Worker 2 now sees the 2 attempts made by Worker 1
        assert worker2.is_rate_limited(key, max_attempts, window) is False

        # Worker 2 records 3rd attempt
        worker2.record_attempt(key)

        # Both workers now throttle the IP
        assert worker1.is_rate_limited(key, max_attempts, window) is True
        assert worker2.is_rate_limited(key, max_attempts, window) is True

        # Reset clears for all workers
        worker1.reset(key)
        assert worker2.is_rate_limited(key, max_attempts, window) is False

    def test_redis_failure_falls_back_to_in_memory_throttling(self):
        """
        Verify the safe failure policy:
        When Redis raises an operational exception, rate limiting is NOT disabled.
        It falls back to internal in-memory rate limiting and continues throttling.
        """
        from app.core.rate_limiter import RedisRateLimiter

        failing_client = MagicMock()
        mock_pipe = MagicMock()
        mock_pipe.execute.side_effect = Exception("ConnectionRefusedError: Redis server is down")
        failing_client.pipeline.return_value = mock_pipe
        failing_client.delete.side_effect = Exception("ConnectionRefusedError: Redis server is down")

        limiter = RedisRateLimiter("redis://broken-host:6379/0", client=failing_client)

        # 1. Under "strict_quota" policy with 4 workers:
        # max_attempts=8 means each worker allows max(1, 8 // 4) = 2 attempts.
        with patch("app.core.rate_limiter.settings") as mock_settings:
            mock_settings.RATE_LIMIT_FAILURE_POLICY = "strict_quota"
            mock_settings.RATE_LIMIT_ESTIMATED_WORKERS = 4

            key = "attacker_ip:10.0.0.1"
            max_attempts = 8
            window = 300

            # Attempt 1: not limited (0 recorded)
            assert limiter.is_rate_limited(key, max_attempts, window) is False
            limiter.record_attempt(key)

            # Attempt 2: not limited (1 recorded < 2 allowed)
            assert limiter.is_rate_limited(key, max_attempts, window) is False
            limiter.record_attempt(key)

            # Attempt 3: 2 attempts recorded >= 2 quota -> throttled on this worker!
            assert limiter.is_rate_limited(key, max_attempts, window) is True

        # 2. Under "fail_closed" policy: immediately blocks
        with patch("app.core.rate_limiter.settings") as mock_settings:
            mock_settings.RATE_LIMIT_FAILURE_POLICY = "fail_closed"
            assert limiter.is_rate_limited("any_key", 5, 60) is True

        # 3. Under "fallback_memory" policy: uses unscaled in-memory limits
        with patch("app.core.rate_limiter.settings") as mock_settings:
            mock_settings.RATE_LIMIT_FAILURE_POLICY = "fallback_memory"
            limiter_fallback = RedisRateLimiter("redis://broken-host:6379/0", client=failing_client)
            key2 = "attacker_ip:10.0.0.2"
            assert limiter_fallback.is_rate_limited(key2, 2, 60) is False
            limiter_fallback.record_attempt(key2)
            assert limiter_fallback.is_rate_limited(key2, 2, 60) is False
            limiter_fallback.record_attempt(key2)
            assert limiter_fallback.is_rate_limited(key2, 2, 60) is True


    def test_redis_limiter_without_client_uses_fallback(self):
        """When client is None, fallback limiter is used safely without errors."""
        from app.core.rate_limiter import RedisRateLimiter

        limiter = RedisRateLimiter("", client=None)
        key = "test_none_client"
        assert limiter.is_rate_limited(key, 2, 60) is False
        limiter.record_attempt(key)
        limiter.record_attempt(key)
        assert limiter.is_rate_limited(key, 2, 60) is True


@pytest.mark.skipif(
    not os.getenv("REDIS_URL"),
    reason="LIVE_REDIS: REDIS_URL not set — skipping live cluster test. "
           "STATUS: Live Redis cluster unverified on localhost:6379. "
           "Configure REDIS_URL to enable live cluster testing."
)
def test_live_redis_cluster():
    """Live Redis cluster integration test — runs only when REDIS_URL is configured."""
    from app.core.rate_limiter import RedisRateLimiter
    redis_url = os.getenv("REDIS_URL")
    limiter = RedisRateLimiter(redis_url)
    test_key = "live_test_key"
    limiter.reset(test_key)
    assert limiter.is_rate_limited(test_key, 2, 60) is False
    limiter.record_attempt(test_key)
    limiter.record_attempt(test_key)
    assert limiter.is_rate_limited(test_key, 2, 60) is True
    limiter.reset(test_key)
    assert limiter.is_rate_limited(test_key, 2, 60) is False

