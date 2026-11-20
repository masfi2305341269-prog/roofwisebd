import os
import secrets
import time
import uuid
import jwt
from datetime import datetime
import pytest
from fastapi.testclient import TestClient
from main import app
from app.core.config import settings
from app.core.security import (
    get_password_hash,
    verify_password,
    validate_password_strength,
    generate_csrf_token,
    verify_csrf_token,
    hash_token,
    set_jwks_client_for_testing
)
from cryptography.hazmat.primitives.asymmetric import ec
from app.database.database import SessionLocal
from app.database.models import User, UserSession, PasswordResetToken, AssessmentRecord

def _safety_check_test_db(db):
    bind_url = str(db.get_bind().url).lower()
    if not ("test" in bind_url or ":memory:" in bind_url):
        raise RuntimeError(
            f"FATAL SAFETY INTERLOCK: clean_db attempted on non-test DB: {bind_url}. "
            "Automated test data deletion is strictly forbidden on non-test databases."
        )

@pytest.fixture(autouse=True)
def clean_db():
    """Clean test data before and after test runs — guarded to run ONLY on isolated test databases."""
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


def test_argon2id_hashing_and_complexity():
    """Verify Argon2id password hashing and complexity enforcement."""
    pw = "BanglaSolar2026!"
    hashed = get_password_hash(pw)
    assert hashed.startswith("$argon2id$")
    assert verify_password(pw, hashed) is True
    assert verify_password("WrongPassword123", hashed) is False

    # Password complexity checks
    valid, _ = validate_password_strength("Short1")
    assert valid is False  # < 8 chars

    valid, _ = validate_password_strength("nocapitalandnonumbers")
    assert valid is False  # no numbers

    valid, _ = validate_password_strength("1234567890")
    assert valid is False  # no letters

    valid, _ = validate_password_strength("ValidPass2026")
    assert valid is True

def test_csrf_token_generation_and_validation():
    """Verify signed session-bound CSRF token issuance and cryptographic verification."""
    token = generate_csrf_token(session_id="guest")
    assert "." in token
    assert verify_csrf_token(token, session_id="guest") is True
    assert verify_csrf_token(token, session_id="other_session") is False

    # Tampered token check
    tampered = token[:-4] + "abcd"
    assert verify_csrf_token(tampered, session_id="guest") is False

def test_csrf_bootstrap_and_protection():
    """Verify CSRF bootstrap endpoint and rejection of state-changing requests without CSRF."""
    client = TestClient(app)
    # 1. State-changing request without CSRF token must fail with 403
    bad_res = client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "Password123",
            "full_name": "Test User"
        }
    )
    assert bad_res.status_code == 403
    assert "CSRF" in bad_res.json()["detail"]

    # 2. Bootstrap CSRF token
    csrf_res = client.get("/api/v1/auth/csrf")
    assert csrf_res.status_code == 200
    csrf_token = csrf_res.json()["csrf_token"]
    assert settings.CSRF_COOKIE_NAME in csrf_res.cookies

    # 3. Successful registration with valid CSRF header and cookie
    headers = {"X-CSRF-Token": csrf_token}
    good_res = client.post(
        "/api/v1/auth/register",
        headers=headers,
        json={
            "email": "resident@roofwisebd.com",
            "password": "SolarPassword2026",
            "full_name": "Rahim Khan",
            "phone": "01700000000",
            "address": "Dhaka"
        }
    )
    assert good_res.status_code == 201
    data = good_res.json()
    assert data["email"] == "resident@roofwisebd.com"
    assert data["role"] == "user"  # Strict default

def test_user_registration_duplicate_and_role_immutability():
    """Verify that duplicate registrations are blocked and users cannot set role=admin."""
    client = TestClient(app)
    csrf_res = client.get("/api/v1/auth/csrf")
    csrf_token = csrf_res.json()["csrf_token"]
    headers = {"X-CSRF-Token": csrf_token}

    # Attempt to pass role="admin"
    res = client.post(
        "/api/v1/auth/register",
        headers=headers,
        json={
            "email": "hacker@example.com",
            "password": "Password123",
            "full_name": "Privilege Escalation Attempt",
            "role": "admin"
        }
    )
    assert res.status_code == 201
    assert res.json()["role"] == "user"  # Backend strictly sets role="user"

    # Duplicate email registration must return 400
    dup_res = client.post(
        "/api/v1/auth/register",
        headers=headers,
        json={
            "email": "hacker@example.com",
            "password": "AnotherPassword123",
            "full_name": "Duplicate"
        }
    )
    assert dup_res.status_code == 400
    assert "already registered" in dup_res.json()["detail"]

def test_user_login_logout_and_session_revocation():
    """Verify login sets HttpOnly cookie, registers session, and logout revokes session."""
    db = SessionLocal()
    user = User(
        email="login_test@roofwisebd.com",
        hashed_password=get_password_hash("ValidPass2026"),
        full_name="Login Test User",
        role="user",
        is_active=True,
        email_verified=True
    )
    db.add(user)
    db.commit()
    db.close()

    client = TestClient(app)
    csrf_res = client.get("/api/v1/auth/csrf")
    csrf_token = csrf_res.json()["csrf_token"]
    headers = {"X-CSRF-Token": csrf_token}

    # Failed login attempt
    bad_login = client.post(
        "/api/v1/auth/login",
        headers=headers,
        json={"email": "login_test@roofwisebd.com", "password": "WrongPassword"}
    )
    assert bad_login.status_code == 401

    # Successful login
    login_res = client.post(
        "/api/v1/auth/login",
        headers=headers,
        json={"email": "login_test@roofwisebd.com", "password": "ValidPass2026"}
    )
    assert login_res.status_code == 200
    assert settings.COOKIE_NAME in client.cookies
    assert settings.CSRF_COOKIE_NAME in client.cookies

    # Verify access to protected /auth/me
    me_res = client.get("/api/v1/auth/me")
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "login_test@roofwisebd.com"

    # Logout with CSRF token
    active_csrf = client.cookies.get(settings.CSRF_COOKIE_NAME)
    logout_res = client.post(
        "/api/v1/auth/logout",
        headers={"X-CSRF-Token": active_csrf}
    )
    assert logout_res.status_code == 200

    # After logout, accessing /auth/me must return 401 Unauthorized
    after_logout = client.get("/api/v1/auth/me")
    assert after_logout.status_code == 401

def test_password_change_and_session_revocation():
    """Verify changing password updates hash and revokes prior sessions."""
    db = SessionLocal()
    user = User(
        email="pw_change@roofwisebd.com",
        hashed_password=get_password_hash("OldPassword2026"),
        full_name="Password Changer",
        role="user",
        is_active=True,
        email_verified=True
    )
    db.add(user)
    db.commit()
    user_id = user.id
    db.close()

    client = TestClient(app)
    csrf_res = client.get("/api/v1/auth/csrf")
    csrf_token = csrf_res.json()["csrf_token"]

    # Log in
    login_res = client.post(
        "/api/v1/auth/login",
        headers={"X-CSRF-Token": csrf_token},
        json={"email": "pw_change@roofwisebd.com", "password": "OldPassword2026"}
    )
    assert login_res.status_code == 200

    # Change password
    active_csrf = client.cookies.get(settings.CSRF_COOKIE_NAME)
    change_res = client.post(
        "/api/v1/auth/change-password",
        headers={"X-CSRF-Token": active_csrf},
        json={"current_password": "OldPassword2026", "new_password": "NewPassword2026"}
    )
    assert change_res.status_code == 200

    # Check DB sessions
    db = SessionLocal()
    sessions = db.query(UserSession).filter(UserSession.user_id == user_id).all()
    assert any(s.revoked is True for s in sessions)
    db.close()

def test_password_reset_flow_and_single_use():
    """Verify forgot-password flow, SHA-256 token hashing, single use, and generic message."""
    db = SessionLocal()
    user = User(
        email="reset_target@roofwisebd.com",
        hashed_password=get_password_hash("InitialPassword2026"),
        full_name="Reset Target",
        role="user",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.close()

    client = TestClient(app)
    csrf_res = client.get("/api/v1/auth/csrf")
    csrf_token = csrf_res.json()["csrf_token"]
    headers = {"X-CSRF-Token": csrf_token}

    # Request reset for existing user
    req_res = client.post(
        "/api/v1/auth/forgot-password",
        headers=headers,
        json={"email": "reset_target@roofwisebd.com"}
    )
    assert req_res.status_code == 200
    assert "instructions have been sent" in req_res.json()["message"]

    # Request reset for non-existing user must return the EXACT same generic message
    non_res = client.post(
        "/api/v1/auth/forgot-password",
        headers=headers,
        json={"email": "nonexistent@example.com"}
    )
    assert non_res.status_code == 200
    assert non_res.json()["message"] == req_res.json()["message"]

    # In dev mode, fetch test token via dev endpoint
    dev_res = client.get("/api/v1/auth/dev/last-reset-token?email=reset_target@roofwisebd.com")
    assert dev_res.status_code == 200
    raw_token = dev_res.json()["token"]

    # Check database stores SHA-256 hash, not raw token
    db = SessionLocal()
    reset_entry = db.query(PasswordResetToken).first()
    assert reset_entry.token_hash == hash_token(raw_token)
    assert reset_entry.token_hash != raw_token
    db.close()

    # Complete reset
    complete_res = client.post(
        "/api/v1/auth/reset-password",
        headers=headers,
        json={"token": raw_token, "new_password": "BrandNewPassword2026"}
    )
    assert complete_res.status_code == 200

    # Attempt to reuse the same reset token must fail (single-use constraint)
    reuse_res = client.post(
        "/api/v1/auth/reset-password",
        headers=headers,
        json={"token": raw_token, "new_password": "AnotherNewPassword2026"}
    )
    assert reuse_res.status_code == 400

def test_admin_rbac_and_privilege_enforcement():
    """Verify regular user cannot access admin routes and admin has full management access."""
    db = SessionLocal()
    regular_user = User(
        email="regular@roofwisebd.com",
        hashed_password=get_password_hash("UserPassword2026"),
        full_name="Regular Citizen",
        role="user",
        is_active=True,
        email_verified=True
    )
    admin_user = User(
        email="admin@roofwisebd.com",
        hashed_password=get_password_hash("AdminPassword2026"),
        full_name="System Admin",
        role="admin",
        is_active=True,
        email_verified=True
    )
    db.add_all([regular_user, admin_user])
    db.commit()
    db.close()

    client = TestClient(app)
    csrf_res = client.get("/api/v1/auth/csrf")
    csrf_token = csrf_res.json()["csrf_token"]
    headers = {"X-CSRF-Token": csrf_token}

    # 1. Regular user logs in and tries to access /api/v1/admin/stats
    client.post(
        "/api/v1/auth/login",
        headers=headers,
        json={"email": "regular@roofwisebd.com", "password": "UserPassword2026"}
    )
    forbidden_res = client.get("/api/v1/admin/stats")
    assert forbidden_res.status_code == 403
    assert "Administrative privileges required" in forbidden_res.json()["detail"]

    # Regular user tries to access /api/v1/auth/admin/login -> rejected
    admin_login_try = client.post(
        "/api/v1/auth/admin/login",
        headers={"X-CSRF-Token": client.cookies.get(settings.CSRF_COOKIE_NAME)},
        json={"email": "regular@roofwisebd.com", "password": "UserPassword2026"}
    )
    assert admin_login_try.status_code == 403

    # 2. Admin logs in via admin portal
    admin_login_res = client.post(
        "/api/v1/auth/admin/login",
        headers={"X-CSRF-Token": client.cookies.get(settings.CSRF_COOKIE_NAME)},
        json={"email": "admin@roofwisebd.com", "password": "AdminPassword2026"}
    )
    assert admin_login_res.status_code == 200

    # Admin accesses /api/v1/admin/stats
    stats_res = client.get("/api/v1/admin/stats")
    assert stats_res.status_code == 200
    stats_data = stats_res.json()
    assert stats_data["total_users"] == 2

def test_guest_assessment_and_secure_claim():
    """Verify guest assessment creates claim_token_hash, and claiming securely binds record."""
    db = SessionLocal()
    user = User(
        email="claim_owner@roofwisebd.com",
        hashed_password=get_password_hash("Password2026"),
        full_name="Claim Owner",
        role="user",
        is_active=True,
        email_verified=True
    )
    db.add(user)
    db.commit()
    user_id = user.id
    db.close()

    client = TestClient(app)
    # Submit assessment as guest
    guest_payload = {
        "location": {"division": "Dhaka", "district": "Dhaka"},
        "consumption": {"monthly_units_kwh": 350.0, "sanctioned_load_kw": 3.0},
        "rooftop": {"total_area_sqft": 1000.0, "roof_type": "concrete_flat", "shading_condition": "low"}
    }
    res = client.post("/api/v1/solar/assessment", json=guest_payload)
    assert res.status_code == 200
    data = res.json()
    assessment_id = data["id"]
    raw_claim_token = data["claim_token"]
    assert raw_claim_token is not None
    assert data["is_guest"] is True

    # Verify DB does NOT contain raw claim token, only SHA-256 hash
    db = SessionLocal()
    record = db.query(AssessmentRecord).filter(AssessmentRecord.id == assessment_id).first()
    assert record.user_id is None
    assert record.claim_token_hash == hash_token(raw_claim_token)
    assert record.claim_token_hash != raw_claim_token
    db.close()

    # Bootstrap CSRF and log in as user
    csrf_res = client.get("/api/v1/auth/csrf")
    csrf_token = csrf_res.json()["csrf_token"]
    client.post(
        "/api/v1/auth/login",
        headers={"X-CSRF-Token": csrf_token},
        json={"email": "claim_owner@roofwisebd.com", "password": "Password2026"}
    )

    active_csrf = client.cookies.get(settings.CSRF_COOKIE_NAME)

    # Attempt to claim with wrong token -> fails 403
    bad_claim = client.post(
        f"/api/v1/solar/assessment/{assessment_id}/claim",
        headers={"X-CSRF-Token": active_csrf},
        json={"claim_token": "WrongSecretToken123456"}
    )
    assert bad_claim.status_code == 403

    # Claim with correct token
    good_claim = client.post(
        f"/api/v1/solar/assessment/{assessment_id}/claim",
        headers={"X-CSRF-Token": active_csrf},
        json={"claim_token": raw_claim_token}
    )
    assert good_claim.status_code == 200
    assert "successfully claimed" in good_claim.json()["message"]

    # Verify ownership in DB and claim_token_hash cleared
    db = SessionLocal()
    record = db.query(AssessmentRecord).filter(AssessmentRecord.id == assessment_id).first()
    assert record.user_id == user_id
    assert record.claim_token_hash is None
    db.close()

def test_tenant_isolation_of_assessments():
    """Verify User A cannot query or view User B's assessments."""
    db = SessionLocal()
    user_a = User(email="user_a@roofwisebd.com", hashed_password=get_password_hash("Pass123456"), full_name="User A", role="user", is_active=True, email_verified=True)
    user_b = User(email="user_b@roofwisebd.com", hashed_password=get_password_hash("Pass123456"), full_name="User B", role="user", is_active=True, email_verified=True)
    db.add_all([user_a, user_b])
    db.commit()

    # Create assessment for User A
    rec_a = AssessmentRecord(
        created_at=datetime.utcnow(),
        user_id=user_a.id,
        division="Dhaka",
        district="Dhaka",
        monthly_units_kwh=400.0,
        total_area_sqft=1200.0,
        usable_area_sqft=800.0,
        recommended_capacity_kwp=4.4,
        recommended_inverter_ac_kw=3.5,
        panel_count=8,
        daily_generation_kwh=16.0,
        monthly_generation_kwh=480.0,
        annual_generation_kwh=5760.0,
        monthly_savings_bdt=3800.0,
        estimated_payback_years=4.2
    )
    db.add(rec_a)
    db.commit()
    rec_a_id = rec_a.id
    db.close()

    client = TestClient(app)
    csrf_res = client.get("/api/v1/auth/csrf")
    csrf_token = csrf_res.json()["csrf_token"]

    # Log in as User B
    client.post(
        "/api/v1/auth/login",
        headers={"X-CSRF-Token": csrf_token},
        json={"email": "user_b@roofwisebd.com", "password": "Pass123456"}
    )

    # User B queries their own assessments -> must be empty
    b_list = client.get("/api/v1/solar/user/assessments")
    assert b_list.status_code == 200
    assert len(b_list.json()) == 0

    # User B attempts to access User A's assessment by ID -> 403 Forbidden
    single_res = client.get(f"/api/v1/solar/assessment/{rec_a_id}")
    assert single_res.status_code == 403


# ---------------------------------------------------------------------------
# Supabase Auth Mode Tests
# ---------------------------------------------------------------------------

FAKE_SUPABASE_JWT_SECRET = "test-supabase-jwt-secret-32-chars-min"

def make_supabase_jwt(
    auth_uid: str,
    email: str,
    role: str = "authenticated",
    exp_offset: int = 3600,
    secret: str = FAKE_SUPABASE_JWT_SECRET,
    aud: str = "authenticated",
    app_metadata: dict = None,
    user_metadata: dict = None,
    email_confirmed: bool = True
) -> str:
    """Generate a fake Supabase-format JWT for testing."""
    payload = {
        "sub": auth_uid,
        "email": email,
        "role": role,
        "aud": aud,
        "iat": int(time.time()),
        "exp": int(time.time()) + exp_offset,
        "email_confirmed_at": "2026-11-19T00:00:00Z" if email_confirmed else None,
        "app_metadata": app_metadata or {"role": "user", "provider": "email"},
        "user_metadata": user_metadata or {"full_name": "Test User", "email_verified": email_confirmed},
    }
    return jwt.encode(payload, secret, algorithm="HS256")


class TestSupabaseAuthMode:
    """Tests for Supabase Auth integration (AUTH_MODE=supabase)."""

    @pytest.fixture(autouse=True)
    def enable_supabase_mode(self, monkeypatch):
        monkeypatch.setattr(settings, "AUTH_MODE", "supabase")
        monkeypatch.setattr(settings, "SUPABASE_JWT_SECRET", FAKE_SUPABASE_JWT_SECRET)
        monkeypatch.setattr(settings, "SUPABASE_URL", "https://test-project.supabase.co")

    def test_supabase_mode_get_me_success(self):
        """With valid JWT and matching auth_user_id in DB, GET /auth/me returns profile."""
        auth_uid = str(uuid.uuid4())
        db = SessionLocal()
        user = User(
            email="supabase_user@roofwisebd.com",
            auth_user_id=auth_uid,
            full_name="Supabase User",
            role="user",
            is_active=True
        )
        db.add(user)
        db.commit()
        db.close()

        token = make_supabase_jwt(auth_uid=auth_uid, email="supabase_user@roofwisebd.com")
        client = TestClient(app, base_url="https://testserver")
        res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})

        assert res.status_code == 200
        data = res.json()
        assert data["email"] == "supabase_user@roofwisebd.com"
        assert data["auth_user_id"] == auth_uid
        assert data["role"] == "user"

    def test_supabase_mode_invalid_jwt(self):
        """Invalid or malformed JWT returns 401 Unauthorized."""
        client = TestClient(app, base_url="https://testserver")

        # 1. Non-JWT string
        res_gibberish = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer not-a-valid-token"})
        assert res_gibberish.status_code == 401
        assert "Invalid or expired access token" in res_gibberish.json()["detail"]

        # 2. Signed with wrong secret
        bad_token = make_supabase_jwt(
            auth_uid=str(uuid.uuid4()),
            email="bad@roofwisebd.com",
            secret="completely-wrong-secret-signature"
        )
        res_bad_sig = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {bad_token}"})
        assert res_bad_sig.status_code == 401

        # 3. Expired token
        expired_token = make_supabase_jwt(
            auth_uid=str(uuid.uuid4()),
            email="expired@roofwisebd.com",
            exp_offset=-3600
        )
        res_expired = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
        assert res_expired.status_code == 401

        # 4. Wrong audience
        wrong_aud_token = make_supabase_jwt(
            auth_uid=str(uuid.uuid4()),
            email="wrong_aud@roofwisebd.com",
            aud="wrong_audience"
        )
        res_wrong_aud = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {wrong_aud_token}"})
        assert res_wrong_aud.status_code == 401

    def test_supabase_mode_no_profile(self):
        """Valid JWT but no matching public.users record returns 401 with profile not found."""
        unprovisioned_uid = str(uuid.uuid4())
        token = make_supabase_jwt(auth_uid=unprovisioned_uid, email="ghost@roofwisebd.com")

        client = TestClient(app, base_url="https://testserver")
        res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})

        assert res.status_code == 401
        assert "User profile not found" in res.json()["detail"]

    def test_supabase_mode_provision_profile(self):
        """POST /auth/provision-profile creates public.users record and is idempotent."""
        auth_uid = str(uuid.uuid4())
        email = "new_registered@roofwisebd.com"
        token = make_supabase_jwt(
            auth_uid=auth_uid,
            email=email,
            user_metadata={"full_name": "New Provisioned Citizen"}
        )

        client = TestClient(app, base_url="https://testserver")

        # First call: provisions fresh profile
        res = client.post("/api/v1/auth/provision-profile", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 201
        data = res.json()
        assert data["email"] == email
        assert data["auth_user_id"] == auth_uid
        assert data["full_name"] == "New Provisioned Citizen"
        assert data["role"] == "user"

        # Verify record exists in DB
        db = SessionLocal()
        created_user = db.query(User).filter(User.auth_user_id == auth_uid).first()
        assert created_user is not None
        assert created_user.email == email
        assert created_user.hashed_password is None
        db.close()

        # Second call: idempotent, returns existing profile
        res_repeat = client.post("/api/v1/auth/provision-profile", headers={"Authorization": f"Bearer {token}"})
        assert res_repeat.status_code in [200, 201]
        assert res_repeat.json()["auth_user_id"] == auth_uid

    def test_supabase_mode_admin_access(self):
        """Admin role check works via public.users.role."""
        admin_uid = str(uuid.uuid4())
        regular_uid = str(uuid.uuid4())

        db = SessionLocal()
        admin_user = User(
            email="admin_sb@roofwisebd.com",
            auth_user_id=admin_uid,
            full_name="Admin Supabase",
            role="admin",
            is_active=True
        )
        reg_user = User(
            email="reg_sb@roofwisebd.com",
            auth_user_id=regular_uid,
            full_name="Regular Supabase",
            role="user",
            is_active=True
        )
        db.add_all([admin_user, reg_user])
        db.commit()
        db.close()

        client = TestClient(app, base_url="https://testserver")

        # 1. Regular user accessing admin route -> 403 Forbidden
        reg_token = make_supabase_jwt(auth_uid=regular_uid, email="reg_sb@roofwisebd.com")
        res_forbidden = client.get("/api/v1/admin/stats", headers={"Authorization": f"Bearer {reg_token}"})
        assert res_forbidden.status_code == 403
        assert "Administrative privileges required" in res_forbidden.json()["detail"]

        # 2. Admin user accessing admin route -> 200 OK
        admin_token = make_supabase_jwt(auth_uid=admin_uid, email="admin_sb@roofwisebd.com")
        res_admin = client.get("/api/v1/admin/stats", headers={"Authorization": f"Bearer {admin_token}"})
        assert res_admin.status_code == 200
        stats = res_admin.json()
        assert "total_users" in stats

    def test_supabase_mode_deactivated_user(self):
        """is_active=False returns 403 Account has been deactivated."""
        deact_uid = str(uuid.uuid4())

        db = SessionLocal()
        deact_user = User(
            email="deactivated_sb@roofwisebd.com",
            auth_user_id=deact_uid,
            full_name="Deactivated SB",
            role="user",
            is_active=False
        )
        db.add(deact_user)
        db.commit()
        db.close()

        token = make_supabase_jwt(auth_uid=deact_uid, email="deactivated_sb@roofwisebd.com")
        client = TestClient(app, base_url="https://testserver")
        res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})

        assert res.status_code == 403
        assert "Account has been deactivated" in res.json()["detail"]

    def test_asymmetric_es256_jwks_verification(self):
        """Asymmetric ES256 tokens are verified via JWKS with 300s cache."""
        private_key = ec.generate_private_key(ec.SECP256R1())
        public_key = private_key.public_key()

        class MockJWK:
            def __init__(self, key):
                self.key = key

        class MockJWKClient:
            def get_signing_key_from_jwt(self, t):
                return MockJWK(public_key)

        set_jwks_client_for_testing(MockJWKClient())

        auth_uid = str(uuid.uuid4())
        db = SessionLocal()
        user = User(
            email="asymmetric_es256@roofwisebd.com",
            auth_user_id=auth_uid,
            full_name="Asymmetric User",
            role="user",
            is_active=True
        )
        db.add(user)
        db.commit()
        db.close()

        payload = {
            "sub": auth_uid,
            "email": "asymmetric_es256@roofwisebd.com",
            "aud": "authenticated",
            "iat": int(time.time()),
            "exp": int(time.time()) + 3600
        }
        token = jwt.encode(payload, private_key, algorithm="ES256", headers={"kid": "key-p256-1"})

        client = TestClient(app, base_url="https://testserver")
        res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})

        set_jwks_client_for_testing(None)

        assert res.status_code == 200
        assert res.json()["email"] == "asymmetric_es256@roofwisebd.com"

    def test_jwks_signing_key_rotation(self):
        """Automatic signing-key rotation resolves new kid, rejects unknown kid."""
        key1 = ec.generate_private_key(ec.SECP256R1())
        key2 = ec.generate_private_key(ec.SECP256R1())

        class MockJWK:
            def __init__(self, key):
                self.key = key

        class RotatedJWKClient:
            def __init__(self):
                self.keyring = {"active-key-1": key1.public_key(), "rotated-key-2": key2.public_key()}

            def get_signing_key_from_jwt(self, t):
                h = jwt.get_unverified_header(t)
                kid = h.get("kid")
                if kid in self.keyring:
                    return MockJWK(self.keyring[kid])
                from jwt import PyJWKClientError
                raise PyJWKClientError(f"Key {kid} not found")

        set_jwks_client_for_testing(RotatedJWKClient())

        auth_uid = str(uuid.uuid4())
        db = SessionLocal()
        user = User(
            email="rotation_test@roofwisebd.com",
            auth_user_id=auth_uid,
            full_name="Rotation User",
            role="user",
            is_active=True
        )
        db.add(user)
        db.commit()
        db.close()

        # Token with rotated key
        token_rotated = jwt.encode(
            {"sub": auth_uid, "email": "rotation_test@roofwisebd.com", "aud": "authenticated", "exp": int(time.time()) + 3600},
            key2, algorithm="ES256", headers={"kid": "rotated-key-2"}
        )
        # Token with unknown key
        token_unknown = jwt.encode(
            {"sub": auth_uid, "email": "rotation_test@roofwisebd.com", "aud": "authenticated", "exp": int(time.time()) + 3600},
            key1, algorithm="ES256", headers={"kid": "unknown-nonexistent-key"}
        )

        client = TestClient(app, base_url="https://testserver")
        res_valid = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token_rotated}"})
        res_invalid = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token_unknown}"})

        set_jwks_client_for_testing(None)

        assert res_valid.status_code == 200
        assert res_invalid.status_code == 401

    def test_legacy_endpoints_disabled_in_supabase_mode(self):
        """Legacy endpoints return 410 Gone when AUTH_MODE=supabase to prevent split-brain passwords."""
        client = TestClient(app, base_url="https://testserver")

        # 1. POST /auth/register
        r_reg = client.post("/api/v1/auth/register", json={
            "email": "legacy_forbidden@roofwisebd.com", "password": "Password123!", "full_name": "Test"
        })
        assert r_reg.status_code == 410
        assert "disabled in Supabase mode" in r_reg.json()["detail"]

        # 2. POST /auth/login
        r_login = client.post("/api/v1/auth/login", json={
            "email": "legacy_forbidden@roofwisebd.com", "password": "Password123!"
        })
        assert r_login.status_code == 410

        # 3. POST /auth/admin/login — NOT blocked in Supabase mode.
        # Admin accounts use legacy Argon2id password permanently; this endpoint
        # has require_legacy_auth_mode removed so admins can still sign in.
        # Will return 401 (bad credentials) or 403, but never 410 Gone.
        r_admin_login = client.post("/api/v1/auth/admin/login", json={
            "email": "admin@roofwisebd.com", "password": "Password123!"
        })
        assert r_admin_login.status_code in (401, 403, 422)  # Not 410

        # 4. POST /auth/change-password
        r_change_pw = client.post("/api/v1/auth/change-password", json={
            "current_password": "Old123!", "new_password": "NewPassword123!"
        })
        assert r_change_pw.status_code == 410

        # 5. POST /auth/forgot-password
        r_forgot = client.post("/api/v1/auth/forgot-password", json={
            "email": "test@roofwisebd.com"
        })
        assert r_forgot.status_code == 410

        # 6. POST /auth/reset-password
        r_reset = client.post("/api/v1/auth/reset-password", json={
            "token": "tok123", "new_password": "NewPassword123!"
        })
        assert r_reset.status_code == 410

        # 7. GET /auth/dev/last-reset-token
        r_dev = client.get("/api/v1/auth/dev/last-reset-token?email=test@roofwisebd.com")
        assert r_dev.status_code == 410

    def test_unverified_email_provision_rejected(self):
        """POST /auth/provision-profile rejects unverified emails with 403 Forbidden."""
        auth_uid = str(uuid.uuid4())
        email = "unconfirmed@roofwisebd.com"
        token = make_supabase_jwt(auth_uid=auth_uid, email=email, email_confirmed=False)

        client = TestClient(app, base_url="https://testserver")
        res = client.post("/api/v1/auth/provision-profile", headers={"Authorization": f"Bearer {token}"})

        assert res.status_code == 403
        assert "must be confirmed" in res.json()["detail"]

    def test_account_takeover_prevention_on_existing_user(self):
        """Public registration cannot claim an existing public.users profile by email."""
        db = SessionLocal()
        legacy_user = User(
            email="existing_victim@roofwisebd.com",
            auth_user_id=None,
            hashed_password=get_password_hash("SecretPassword123!"),
            full_name="Victim User",
            role="user",
            is_active=True
        )
        db.add(legacy_user)
        db.commit()
        db.close()

        # Attacker registers on Supabase with the victim's email and tries to provision
        attacker_uid = str(uuid.uuid4())
        token = make_supabase_jwt(auth_uid=attacker_uid, email="existing_victim@roofwisebd.com", email_confirmed=True)

        client = TestClient(app, base_url="https://testserver")
        res = client.post("/api/v1/auth/provision-profile", headers={"Authorization": f"Bearer {token}"})

        # MUST return 409 Conflict and NOT link the account
        assert res.status_code == 409
        assert "Automatic account linking is disabled" in res.json()["detail"]

        # Verify profile was untouched
        db = SessionLocal()
        check = db.query(User).filter(User.email == "existing_victim@roofwisebd.com").first()
        assert check.auth_user_id is None
        db.close()

    def test_account_takeover_prevention_on_admin_user(self):
        """Public registration cannot claim the existing admin profile."""
        db = SessionLocal()
        admin_user = User(
            email="admin@roofwisebd.com",
            auth_user_id=None,
            hashed_password=get_password_hash("AdminPass123!"),
            full_name="Admin Roofwise",
            role="admin",
            is_active=True
        )
        db.add(admin_user)
        db.commit()
        db.close()

        attacker_uid = str(uuid.uuid4())
        token = make_supabase_jwt(auth_uid=attacker_uid, email="admin@roofwisebd.com", email_confirmed=True)

        client = TestClient(app, base_url="https://testserver")
        res = client.post("/api/v1/auth/provision-profile", headers={"Authorization": f"Bearer {token}"})

        assert res.status_code == 409

        db = SessionLocal()
        admin_check = db.query(User).filter(User.email == "admin@roofwisebd.com").first()
        assert admin_check.auth_user_id is None
        assert admin_check.role == "admin"
        db.close()

    def test_link_legacy_account_refuses_admin(self):
        """Admin accounts cannot be linked via public POST /auth/link-legacy-account."""
        db = SessionLocal()
        admin_user = User(
            email="admin_link_test@roofwisebd.com",
            auth_user_id=None,
            hashed_password=get_password_hash("AdminPass123!"),
            full_name="Admin Test",
            role="admin",
            is_active=True
        )
        db.add(admin_user)
        db.commit()
        db.close()

        token = make_supabase_jwt(auth_uid=str(uuid.uuid4()), email="admin_link_test@roofwisebd.com")
        client = TestClient(app, base_url="https://testserver")
        res = client.post(
            "/api/v1/auth/link-legacy-account",
            headers={"Authorization": f"Bearer {token}"},
            json={"legacy_password": "AdminPass123!"}
        )

        assert res.status_code == 403
        assert "Administrative accounts cannot be linked" in res.json()["detail"]

    def test_link_legacy_account_wrong_password(self):
        """Legacy account linking fails with 401 if submitted password does not match hash."""
        db = SessionLocal()
        user = User(
            email="legacy_user_link@roofwisebd.com",
            auth_user_id=None,
            hashed_password=get_password_hash("CorrectPassword123!"),
            full_name="Legacy Link",
            role="user",
            is_active=True
        )
        db.add(user)
        db.commit()
        db.close()

        token = make_supabase_jwt(auth_uid=str(uuid.uuid4()), email="legacy_user_link@roofwisebd.com")
        client = TestClient(app, base_url="https://testserver")
        res = client.post(
            "/api/v1/auth/link-legacy-account",
            headers={"Authorization": f"Bearer {token}"},
            json={"legacy_password": "WrongPassword123!"}
        )

        assert res.status_code == 401
        assert "verification failed" in res.json()["detail"]

    def test_link_legacy_account_success(self):
        """Legacy account linking succeeds with correct password, links auth_user_id, and retires hash."""
        db = SessionLocal()
        user = User(
            email="legit_legacy@roofwisebd.com",
            auth_user_id=None,
            hashed_password=get_password_hash("MySecret123!"),
            full_name="Legit Legacy",
            role="user",
            is_active=True
        )
        db.add(user)
        db.commit()
        user_id = user.id
        db.close()

        auth_uid = str(uuid.uuid4())
        token = make_supabase_jwt(auth_uid=auth_uid, email="legit_legacy@roofwisebd.com")
        client = TestClient(app, base_url="https://testserver")
        res = client.post(
            "/api/v1/auth/link-legacy-account",
            headers={"Authorization": f"Bearer {token}"},
            json={"legacy_password": "MySecret123!"}
        )

        assert res.status_code == 200
        data = res.json()
        assert data["email"] == "legit_legacy@roofwisebd.com"
        assert data["auth_user_id"] == auth_uid

        # Verify DB: auth_user_id set, hashed_password nulled
        db = SessionLocal()
        updated = db.query(User).filter(User.id == user_id).first()
        assert updated.auth_user_id == auth_uid
        assert updated.hashed_password is None
        db.close()

    def test_supabase_mode_assessment_isolation_and_guest_claim(self):
        """Tests assessment ownership, cross-user isolation, and guest assessment claim in Supabase mode."""
        client = TestClient(app, base_url="https://testserver")

        # 1. Guest creates assessment
        guest_payload = {
            "location": {"division": "Dhaka", "district": "Dhaka"},
            "consumption": {"monthly_units_kwh": 350.0, "sanctioned_load_kw": 3.0},
            "rooftop": {"total_area_sqft": 1000.0, "roof_type": "concrete_flat", "shading_condition": "low"}
        }
        res_create = client.post("/api/v1/solar/assessment", json=guest_payload)
        assert res_create.status_code == 200
        assessment_data = res_create.json()
        assessment_id = assessment_data["id"]
        claim_token = assessment_data["claim_token"]
        assert claim_token is not None

        # 2. Provision Supabase User A
        user_a_uid = str(uuid.uuid4())
        user_a_token = make_supabase_jwt(auth_uid=user_a_uid, email="user_a_sb@roofwisebd.com")
        client.post("/api/v1/auth/provision-profile", headers={"Authorization": f"Bearer {user_a_token}"})

        # 3. User A claims the guest assessment
        res_claim = client.post(
            f"/api/v1/solar/assessment/{assessment_id}/claim",
            headers={"Authorization": f"Bearer {user_a_token}"},
            json={"claim_token": claim_token}
        )
        assert res_claim.status_code == 200
        assert "claimed" in res_claim.json()["message"].lower()

        # 4. User A can view their claimed assessment
        res_view = client.get(
            f"/api/v1/solar/assessment/{assessment_id}",
            headers={"Authorization": f"Bearer {user_a_token}"}
        )
        assert res_view.status_code == 200

        # 5. Provision Supabase User B
        user_b_uid = str(uuid.uuid4())
        user_b_token = make_supabase_jwt(auth_uid=user_b_uid, email="user_b_sb@roofwisebd.com")
        client.post("/api/v1/auth/provision-profile", headers={"Authorization": f"Bearer {user_b_token}"})

        # 6. User B attempts to view User A's assessment -> 403 Forbidden (cross-user isolation)
        res_user_b = client.get(
            f"/api/v1/solar/assessment/{assessment_id}",
            headers={"Authorization": f"Bearer {user_b_token}"}
        )
        assert res_user_b.status_code == 403

    def test_supabase_mode_admin_legacy_login_and_access(self):
        """Verifies admin logs in via /admin/login in Supabase mode and accesses admin routes."""
        db = SessionLocal()
        # Seed an admin user with Argon2id password
        admin_email = "superadmin_sb@roofwisebd.com"
        admin = User(
            email=admin_email,
            hashed_password=get_password_hash("AdminMasterPass123!"),
            full_name="Super Admin",
            role="admin",
            is_active=True,
            email_verified=True
        )
        db.add(admin)
        db.commit()
        db.close()

        client = TestClient(app, base_url="https://testserver")
        # Bootstrap CSRF
        csrf_res = client.get("/api/v1/auth/csrf")
        csrf_token = csrf_res.json()["csrf_token"]

        # Admin logs in via legacy Argon2id credentials
        res_login = client.post(
            "/api/v1/auth/admin/login",
            json={"email": admin_email, "password": "AdminMasterPass123!"},
            headers={"X-CSRF-Token": csrf_token}
        )
        assert res_login.status_code == 200
        assert res_login.json()["role"] == "admin"

        # Admin accesses admin stats and /me using the session cookie established
        res_stats = client.get("/api/v1/admin/stats")
        assert res_stats.status_code == 200

        res_me = client.get("/api/v1/auth/me")
        assert res_me.status_code == 200
        assert res_me.json()["email"] == admin_email

    def test_supabase_mode_legacy_user_linking_preserves_assessments(self):
        """Verifies existing assessments remain linked to user after Supabase linking."""
        from app.database.models import AssessmentRecord
        db = SessionLocal()
        legacy_email = "assessment_owner@roofwisebd.com"
        user = User(
            email=legacy_email,
            hashed_password=get_password_hash("OwnerSecret123!"),
            full_name="Assessment Owner",
            role="user",
            is_active=True,
            email_verified=True
        )
        db.add(user)
        db.commit()
        user_id = user.id

        # Attach historical assessment record
        rec = AssessmentRecord(
            user_id=user_id,
            claim_token_hash=hash_token("historical_claim_tok"),
            division="Chittagong",
            district="Cox's Bazar",
            monthly_units_kwh=420.0,
            billing_period_days=30,
            sanctioned_load_kw=4.0,
            total_area_sqft=1500.0,
            usable_area_sqft=1050.0,
            recommended_capacity_kwp=3.5,
            recommended_inverter_ac_kw=3.0,
            panel_count=8,
            daily_generation_kwh=14.0,
            monthly_generation_kwh=430.0,
            annual_generation_kwh=5160.0,
            monthly_savings_bdt=3800.0,
            estimated_payback_years=4.8,
            sreda_compliant=True
        )
        db.add(rec)
        db.commit()
        rec_id = rec.id
        db.close()

        client = TestClient(app, base_url="https://testserver")
        auth_uid = str(uuid.uuid4())
        token = make_supabase_jwt(auth_uid=auth_uid, email=legacy_email)

        # Link legacy account to Supabase Auth
        res_link = client.post(
            "/api/v1/auth/link-legacy-account",
            headers={"Authorization": f"Bearer {token}"},
            json={"legacy_password": "OwnerSecret123!"}
        )
        assert res_link.status_code == 200

        # Query assessments with Supabase JWT
        res_history = client.get(
            "/api/v1/solar/user/assessments",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert res_history.status_code == 200
        history = res_history.json()
        assert len(history) == 1
        assert history[0]["id"] == rec_id
        assert history[0]["district"] == "Cox's Bazar"


