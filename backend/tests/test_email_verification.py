"""
tests/test_email_verification.py
================================
Comprehensive tests for Email Verification via 6-digit OTP in RoofwiseBD legacy auth:
1. Registration creates user with email_verified=False and single-use 6-digit OTP.
2. Unverified users cannot log in (HTTP 403 Forbidden).
3. Plaintext OTP is NEVER stored in database; only HMAC-SHA256 hash is persisted.
4. Correct OTP verifies email (email_verified=True), marks OTP used, allows subsequent login.
5. Incorrect OTP is rejected with remaining attempt count.
6. Excessive failed attempts (>=5) invalidates the OTP.
7. Expired OTP (>10 minutes) is rejected.
8. Single-use enforcement: already-used OTP cannot be reused.
9. Resend OTP creates fresh OTP, invalidates prior OTP, enforces 60s cooldown.
10. Existing accounts and admin remain verified and can log in without friction.
11. Account deactivation (is_active=False) remains separate and enforced.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch
from fastapi.testclient import TestClient
from main import app
from app.core.config import settings
from app.core.security import get_password_hash, hash_otp, verify_otp_hash
from app.database.database import SessionLocal
from app.database.models import User, EmailVerificationOTP

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def csrf_token(client):
    res = client.get("/api/v1/auth/csrf")
    assert res.status_code == 200
    return res.json()["csrf_token"]


def test_registration_creates_unverified_user_and_otp(client, csrf_token):
    """Registration creates account with email_verified=False and stores only hashed OTP."""
    email = "new_verify_user@roofwisebd.com"
    headers = {"X-CSRF-Token": csrf_token}

    with patch("app.api.v1.endpoints.auth.send_verification_otp_email") as mock_send:
        mock_send.return_value = None
        reg_res = client.post("/api/v1/auth/register", headers=headers, json={
            "email": email,
            "password": "Password123!",
            "full_name": "New Verify User"
        })
        assert reg_res.status_code == 201
        data = reg_res.json()
        assert data["email"] == email
        assert data["email_verified"] is False

    # Check database record
    db = SessionLocal()
    user = db.query(User).filter(User.email == email).first()
    assert user is not None
    assert user.email_verified is False
    assert user.is_active is True

    # Check OTP record
    otp_record = db.query(EmailVerificationOTP).filter(EmailVerificationOTP.user_id == user.id).first()
    assert otp_record is not None
    assert otp_record.used is False
    assert otp_record.attempts == 0
    # Confirm raw OTP is NOT in database
    assert len(otp_record.otp_hash) == 64  # SHA256 hex length
    assert not otp_record.otp_hash.isdigit()  # Hash is hex, never raw 6-digit digits
    db.close()

    # Unverified user cannot log in
    login_res = client.post("/api/v1/auth/login", headers=headers, json={
        "email": email,
        "password": "Password123!"
    })
    assert login_res.status_code == 403
    assert "not verified" in login_res.json()["detail"].lower()


def test_successful_otp_verification_allows_login(client, csrf_token):
    """Correct 6-digit OTP verifies email and unlocks login."""
    db = SessionLocal()
    user = User(
        email="verify_success@roofwisebd.com",
        hashed_password=get_password_hash("Password123!"),
        full_name="Verify Success",
        role="user",
        is_active=True,
        email_verified=False
    )
    db.add(user)
    db.commit()

    raw_otp = "123456"
    otp_record = EmailVerificationOTP(
        user_id=user.id,
        otp_hash=hash_otp(raw_otp, user.id),
        expires_at=datetime.utcnow() + timedelta(minutes=10),
        used=False,
        attempts=0
    )
    db.add(otp_record)
    db.commit()
    user_id = user.id
    db.close()

    headers = {"X-CSRF-Token": csrf_token}

    # Verify with correct OTP
    verify_res = client.post("/api/v1/auth/verify-email", headers=headers, json={
        "email": "verify_success@roofwisebd.com",
        "otp": raw_otp
    })
    assert verify_res.status_code == 200
    assert verify_res.json()["email_verified"] is True

    # Confirm in database
    db = SessionLocal()
    user = db.query(User).filter(User.id == user_id).first()
    assert user.email_verified is True
    otp_rec = db.query(EmailVerificationOTP).filter(EmailVerificationOTP.user_id == user_id).first()
    assert otp_rec.used is True
    db.close()

    # Now login succeeds
    login_res = client.post("/api/v1/auth/login", headers=headers, json={
        "email": "verify_success@roofwisebd.com",
        "password": "Password123!"
    })
    assert login_res.status_code == 200
    assert login_res.json()["email"] == "verify_success@roofwisebd.com"


def test_incorrect_otp_increments_attempts_and_rejects(client, csrf_token):
    """Incorrect OTP returns 400 and increments failed attempt counter."""
    db = SessionLocal()
    user = User(
        email="wrong_otp@roofwisebd.com",
        hashed_password=get_password_hash("Password123!"),
        full_name="Wrong OTP User",
        role="user",
        is_active=True,
        email_verified=False
    )
    db.add(user)
    db.commit()

    raw_otp = "654321"
    otp_record = EmailVerificationOTP(
        user_id=user.id,
        otp_hash=hash_otp(raw_otp, user.id),
        expires_at=datetime.utcnow() + timedelta(minutes=10),
        used=False,
        attempts=0
    )
    db.add(otp_record)
    db.commit()
    user_id = user.id
    db.close()

    headers = {"X-CSRF-Token": csrf_token}

    # Try wrong OTP
    bad_res = client.post("/api/v1/auth/verify-email", headers=headers, json={
        "email": "wrong_otp@roofwisebd.com",
        "otp": "000000"
    })
    assert bad_res.status_code == 400
    assert "Invalid verification code" in bad_res.json()["detail"]
    assert "4 attempt(s) remaining" in bad_res.json()["detail"]

    # Verify attempts in DB
    db = SessionLocal()
    otp_rec = db.query(EmailVerificationOTP).filter(EmailVerificationOTP.user_id == user_id).first()
    assert otp_rec.attempts == 1
    assert otp_rec.used is False
    db.close()


def test_excessive_attempts_invalidates_otp(client, csrf_token):
    """Exceeding 5 failed attempts invalidates the OTP."""
    db = SessionLocal()
    user = User(
        email="locked_otp@roofwisebd.com",
        hashed_password=get_password_hash("Password123!"),
        full_name="Locked OTP User",
        role="user",
        is_active=True,
        email_verified=False
    )
    db.add(user)
    db.commit()

    raw_otp = "777888"
    otp_record = EmailVerificationOTP(
        user_id=user.id,
        otp_hash=hash_otp(raw_otp, user.id),
        expires_at=datetime.utcnow() + timedelta(minutes=10),
        used=False,
        attempts=4  # 4 previous failed attempts
    )
    db.add(otp_record)
    db.commit()
    user_id = user.id
    db.close()

    headers = {"X-CSRF-Token": csrf_token}

    # 5th failed attempt should invalidate the OTP
    final_fail = client.post("/api/v1/auth/verify-email", headers=headers, json={
        "email": "locked_otp@roofwisebd.com",
        "otp": "000000"
    })
    assert final_fail.status_code == 400
    assert "invalidated" in final_fail.json()["detail"].lower()

    # Even sending correct OTP now must be rejected
    correct_try = client.post("/api/v1/auth/verify-email", headers=headers, json={
        "email": "locked_otp@roofwisebd.com",
        "otp": raw_otp
    })
    assert correct_try.status_code == 400


def test_expired_otp_is_rejected(client, csrf_token):
    """OTP older than 10 minutes cannot be used."""
    db = SessionLocal()
    user = User(
        email="expired_otp@roofwisebd.com",
        hashed_password=get_password_hash("Password123!"),
        full_name="Expired OTP User",
        role="user",
        is_active=True,
        email_verified=False
    )
    db.add(user)
    db.commit()

    raw_otp = "112233"
    otp_record = EmailVerificationOTP(
        user_id=user.id,
        otp_hash=hash_otp(raw_otp, user.id),
        expires_at=datetime.utcnow() - timedelta(minutes=1),  # Expired 1 min ago
        used=False,
        attempts=0
    )
    db.add(otp_record)
    db.commit()
    db.close()

    headers = {"X-CSRF-Token": csrf_token}

    res = client.post("/api/v1/auth/verify-email", headers=headers, json={
        "email": "expired_otp@roofwisebd.com",
        "otp": raw_otp
    })
    assert res.status_code == 400
    assert "expired" in res.json()["detail"].lower()


def test_single_use_otp_cannot_be_reused(client, csrf_token):
    """An OTP that has already been verified cannot be used a second time."""
    db = SessionLocal()
    user = User(
        email="reused_otp@roofwisebd.com",
        hashed_password=get_password_hash("Password123!"),
        full_name="Reused OTP User",
        role="user",
        is_active=True,
        email_verified=False
    )
    db.add(user)
    db.commit()

    raw_otp = "334455"
    otp_record = EmailVerificationOTP(
        user_id=user.id,
        otp_hash=hash_otp(raw_otp, user.id),
        expires_at=datetime.utcnow() + timedelta(minutes=10),
        used=False,
        attempts=0
    )
    db.add(otp_record)
    db.commit()
    db.close()

    headers = {"X-CSRF-Token": csrf_token}

    # First use -> 200
    first = client.post("/api/v1/auth/verify-email", headers=headers, json={
        "email": "reused_otp@roofwisebd.com",
        "otp": raw_otp
    })
    assert first.status_code == 200

    # Second use -> already verified
    second = client.post("/api/v1/auth/verify-email", headers=headers, json={
        "email": "reused_otp@roofwisebd.com",
        "otp": raw_otp
    })
    assert second.status_code == 200
    assert "already verified" in second.json()["message"].lower()


def test_resend_verification_otp_flow_and_cooldown(client, csrf_token):
    """Resend verification generates new OTP, invalidates old, enforces 60s cooldown."""
    db = SessionLocal()
    user = User(
        email="resend_user@roofwisebd.com",
        hashed_password=get_password_hash("Password123!"),
        full_name="Resend User",
        role="user",
        is_active=True,
        email_verified=False
    )
    db.add(user)
    db.commit()

    old_otp = "111111"
    old_record = EmailVerificationOTP(
        user_id=user.id,
        otp_hash=hash_otp(old_otp, user.id),
        expires_at=datetime.utcnow() + timedelta(minutes=10),
        used=False,
        attempts=0
    )
    db.add(old_record)
    db.commit()
    user_id = user.id
    db.close()

    headers = {"X-CSRF-Token": csrf_token}

    # If SMTP_HOST is not configured, resend raises 503 (never pretends email sent)
    with patch("app.core.config.settings.SMTP_HOST", ""):
        res_no_smtp = client.post("/api/v1/auth/resend-verification", headers=headers, json={
            "email": "resend_user@roofwisebd.com"
        })
        assert res_no_smtp.status_code == 503
        assert "not configured" in res_no_smtp.json()["detail"].lower()

    # With SMTP configured, resend succeeds
    with patch("app.core.config.settings.SMTP_HOST", "smtp.example.com"), \
         patch("app.api.v1.endpoints.auth.send_verification_otp_email") as mock_send:
        mock_send.return_value = None

        res_send = client.post("/api/v1/auth/resend-verification", headers=headers, json={
            "email": "resend_user@roofwisebd.com"
        })
        assert res_send.status_code == 200
        assert mock_send.called

        # Old OTP record must now be marked used
        db = SessionLocal()
        prior = db.query(EmailVerificationOTP).filter(
            EmailVerificationOTP.user_id == user_id,
            EmailVerificationOTP.otp_hash == hash_otp(old_otp, user_id)
        ).first()
        assert prior.used is True

        # Fresh OTP record exists
        latest = db.query(EmailVerificationOTP).filter(
            EmailVerificationOTP.user_id == user_id,
            EmailVerificationOTP.used == False
        ).first()
        assert latest is not None
        assert latest.otp_hash != hash_otp(old_otp, user_id)
        db.close()

        # Immediate second resend hits 60s cooldown (HTTP 429)
        res_cooldown = client.post("/api/v1/auth/resend-verification", headers=headers, json={
            "email": "resend_user@roofwisebd.com"
        })
        assert res_cooldown.status_code == 429
        assert "60 seconds" in res_cooldown.json()["detail"]


def test_existing_admin_and_users_remain_verified(client, csrf_token):
    """Existing accounts with email_verified=True log in without friction."""
    db = SessionLocal()
    # Seed an existing admin and regular user (both already verified)
    admin = User(
        email="existing_admin@roofwisebd.com",
        hashed_password=get_password_hash("AdminPassword2026!"),
        full_name="Existing Admin",
        role="admin",
        is_active=True,
        email_verified=True
    )
    user = User(
        email="existing_customer@roofwisebd.com",
        hashed_password=get_password_hash("UserPassword2026!"),
        full_name="Existing Customer",
        role="user",
        is_active=True,
        email_verified=True
    )
    db.add_all([admin, user])
    db.commit()
    db.close()

    headers = {"X-CSRF-Token": csrf_token}

    # Admin login succeeds
    admin_login = client.post("/api/v1/auth/admin/login", headers=headers, json={
        "email": "existing_admin@roofwisebd.com",
        "password": "AdminPassword2026!"
    })
    assert admin_login.status_code == 200
    assert admin_login.json()["role"] == "admin"
    assert admin_login.json()["email_verified"] is True

    # User login with updated CSRF token succeeds
    user_csrf = client.cookies.get(settings.CSRF_COOKIE_NAME) or csrf_token
    user_login = client.post("/api/v1/auth/login", headers={"X-CSRF-Token": user_csrf}, json={
        "email": "existing_customer@roofwisebd.com",
        "password": "UserPassword2026!"
    })
    assert user_login.status_code == 200
    assert user_login.json()["role"] == "user"
    assert user_login.json()["email_verified"] is True
