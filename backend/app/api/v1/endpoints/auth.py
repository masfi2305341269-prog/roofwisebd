import logging
import os
import secrets
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    get_password_hash,
    verify_password,
    validate_password_strength,
    create_access_token,
    decode_access_token,
    generate_csrf_token,
    hash_token,
    generate_numeric_otp,
    hash_otp,
    verify_otp_hash,
)
from app.core.rate_limiter import get_rate_limiter
from app.core.email import (
    send_password_reset_email,
    send_verification_otp_email,
    EmailDeliveryError,
)
from app.core.validation import (
    validate_full_name,
    validate_bangladesh_phone,
    validate_bangladesh_district,
    validate_email_format,
)
from app.database.database import get_db
from app.database.models import User, UserSession, PasswordResetToken, EmailVerificationOTP
from app.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    UserSummaryResponse,
    UserProfileUpdateRequest,
    ChangePasswordRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    LinkLegacyAccountRequest,
    CSRFResponse,
    VerifyEmailRequest,
    ResendVerificationRequest,
)
from app.api.deps import get_current_user, verify_csrf, extract_token_from_request

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["User Authentication & Account Management"])


def require_legacy_auth_mode():
    """
    Blocks execution of legacy password and session endpoints when AUTH_MODE=supabase.
    Prevents parallel split-brain password systems and legacy login bypasses.
    """
    if settings.AUTH_MODE == "supabase":
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Legacy password authentication endpoints are disabled in Supabase mode. Use Supabase Auth."
        )


@router.get("/csrf", response_model=CSRFResponse, summary="Bootstrap Initial CSRF Token")
def get_csrf_token(request: Request, response: Response):
    """
    Issues an initial signed CSRF token for unauthenticated visitors so registration,
    login, and initial assessment requests can be safely performed with CSRF protection.
    """
    # Check if visitor already has an active session
    token = extract_token_from_request(request)
    session_id = "guest"
    if token:
        payload = decode_access_token(token)
        if payload and payload.get("jti"):
            session_id = payload["jti"]

    csrf_token = generate_csrf_token(session_id=session_id)
    response.set_cookie(
        key=settings.CSRF_COOKIE_NAME,
        value=csrf_token,
        httponly=False,  # Readable by frontend JS to submit in X-CSRF-Token header
        samesite=settings.COOKIE_SAMESITE,
        secure=settings.COOKIE_SECURE,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/"
    )
    return CSRFResponse(csrf_token=csrf_token)


@router.post(
    "/register",
    response_model=UserSummaryResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_legacy_auth_mode), Depends(verify_csrf)],
    summary="User Registration"
)
def register_user(req: UserRegisterRequest, db: Session = Depends(get_db)):
    """
    Registers a new standard residential user.
    Role is strictly hardcoded to 'user' on the backend to prevent privilege escalation.
    """
    # 0. Email Format Validation (defense-in-depth on route level)
    is_valid_email, err_email = validate_email_format(req.email)
    if not is_valid_email:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=err_email)

    # 1. Full Name Validation
    is_valid_name, err_name = validate_full_name(req.full_name)
    if not is_valid_name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err_name)

    # 2. Password Strength Validation
    is_valid_pw, err_pw = validate_password_strength(req.password)
    if not is_valid_pw:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err_pw)

    # 3. Bangladesh Phone Validation
    is_valid_phone, norm_phone, err_phone = validate_bangladesh_phone(req.phone)
    if not is_valid_phone:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err_phone)

    # 4. Bangladesh District Validation
    is_valid_dist, norm_dist, err_dist = validate_bangladesh_district(req.address)
    if not is_valid_dist:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err_dist)

    existing = db.query(User).filter(User.email == req.email.lower()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email is already registered."
        )

    user = User(
        email=req.email.lower(),
        hashed_password=get_password_hash(req.password),
        full_name=req.full_name.strip(),
        phone=norm_phone,
        address=norm_dist,
        role="user",
        is_active=True,
        email_verified=False
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Generate cryptographically secure 6-digit OTP
    raw_otp = generate_numeric_otp(6)
    otp_record = EmailVerificationOTP(
        user_id=user.id,
        otp_hash=hash_otp(raw_otp, user.id),
        expires_at=datetime.utcnow() + timedelta(minutes=10),
        used=False,
        attempts=0
    )
    db.add(otp_record)
    db.commit()

    # Attempt to dispatch email via SMTP (if configured)
    if settings.SMTP_HOST:
        try:
            send_verification_otp_email(to_email=user.email, otp=raw_otp)
        except EmailDeliveryError as exc:
            logger.warning(
                "Verification OTP email delivery failed for user_id=%s: %s",
                user.id, str(exc)
            )
    else:
        logger.info(
            "SMTP_HOST is not configured. Verification email was not sent for user_id=%s.",
            user.id
        )

    return user


@router.post(
    "/verify-email",
    dependencies=[Depends(require_legacy_auth_mode), Depends(verify_csrf)],
    summary="Verify User Email via 6-Digit OTP"
)
def verify_email(
    req: VerifyEmailRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Verifies user email using a 6-digit single-use OTP.
    After successful verification, sets email_verified=True and enables account login.
    Enforces maximum 5 attempts per OTP and global rate limiting.
    """
    limiter = get_rate_limiter()
    client_ip = request.client.host if request.client else "unknown"
    rate_key = f"verify_email:{client_ip}:{req.email}"

    if limiter.is_rate_limited(rate_key, max_attempts=10, window_seconds=300):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many verification attempts. Please wait 5 minutes before trying again."
        )
    limiter.record_attempt(rate_key)

    user = db.query(User).filter(User.email == req.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No account found with this email address."
        )

    if user.email_verified:
        return {
            "message": "Email is already verified. You can now sign in.",
            "email_verified": True
        }

    # Find the latest unused, non-expired OTP record for this user
    otp_record = db.query(EmailVerificationOTP).filter(
        EmailVerificationOTP.user_id == user.id,
        EmailVerificationOTP.used == False,
        EmailVerificationOTP.expires_at > datetime.utcnow()
    ).order_by(EmailVerificationOTP.created_at.desc()).first()

    if not otp_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification code has expired or does not exist. Please request a new code."
        )

    # Check if attempts exceeded on this OTP
    if otp_record.attempts >= 5:
        otp_record.used = True
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Too many failed attempts. This code has been invalidated. Please request a new code."
        )

    if not verify_otp_hash(req.otp, user.id, otp_record.otp_hash):
        otp_record.attempts += 1
        db.commit()
        remaining = 5 - otp_record.attempts
        if remaining <= 0:
            otp_record.used = True
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Too many failed attempts. This code has been invalidated. Please request a new code."
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid verification code. {remaining} attempt(s) remaining."
        )

    # Success: mark OTP as used, verify user email
    otp_record.used = True
    user.email_verified = True
    db.commit()
    db.refresh(user)
    limiter.reset(rate_key)

    return {
        "message": "Email verified successfully! You can now sign in.",
        "email_verified": True
    }


@router.post(
    "/resend-verification",
    dependencies=[Depends(require_legacy_auth_mode), Depends(verify_csrf)],
    summary="Resend Email Verification OTP"
)
def resend_verification(
    req: ResendVerificationRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Generates and dispatches a fresh 6-digit verification code.
    Enforces 60-second cooldown between resends and maximum 5 resends per 15 minutes.
    Never pretends an email was delivered when SMTP is not configured or fails.
    """
    limiter = get_rate_limiter()
    client_ip = request.client.host if request.client else "unknown"
    rate_key = f"resend_otp:{client_ip}:{req.email}"
    cooldown_key = f"resend_cooldown:{req.email}"

    if limiter.is_rate_limited(cooldown_key, max_attempts=1, window_seconds=60):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Please wait 60 seconds before requesting another verification code."
        )

    if limiter.is_rate_limited(rate_key, max_attempts=5, window_seconds=900):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many resend requests. Please wait 15 minutes before trying again."
        )

    user = db.query(User).filter(User.email == req.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No account found with this email address."
        )

    if user.email_verified:
        return {
            "message": "Email is already verified. You can sign in.",
            "email_verified": True
        }

    # Invalidate all prior unused OTPs for this user
    db.query(EmailVerificationOTP).filter(
        EmailVerificationOTP.user_id == user.id,
        EmailVerificationOTP.used == False
    ).update({"used": True})

    # Generate new OTP
    raw_otp = generate_numeric_otp(6)
    otp_record = EmailVerificationOTP(
        user_id=user.id,
        otp_hash=hash_otp(raw_otp, user.id),
        expires_at=datetime.utcnow() + timedelta(minutes=10),
        used=False,
        attempts=0
    )
    db.add(otp_record)
    db.commit()

    # Deliver via SMTP — never pretend delivery if SMTP fails or is missing
    if not settings.SMTP_HOST:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Email delivery service is currently not configured (SMTP_HOST is missing). Please contact support."
        )

    try:
        send_verification_otp_email(to_email=user.email, otp=raw_otp)
    except EmailDeliveryError as exc:
        logger.error("Failed to send verification OTP to %s: %s", user.email, exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to send verification email. Please check your SMTP settings and try again."
        )

    limiter.record_attempt(cooldown_key)
    limiter.record_attempt(rate_key)

    return {
        "message": "A new 6-digit verification code has been sent to your email.",
        "email": user.email
    }


@router.post(
    "/login",
    response_model=UserSummaryResponse,
    dependencies=[Depends(require_legacy_auth_mode), Depends(verify_csrf)],
    summary="User Login (Sets HttpOnly Cookie)"
)
def login_user(
    req: UserLoginRequest,
    response: Response,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Authenticates user, creates a server-side session, and issues an HttpOnly, Secure,
    SameSite cookie containing the JWT, plus a new session-bound CSRF token.
    """
    limiter = get_rate_limiter()
    rate_key = f"login:{req.email.lower()}"
    client_ip = request.client.host if request.client else "unknown"
    ip_key = f"login_ip:{client_ip}"

    if limiter.is_rate_limited(rate_key, max_attempts=5, window_seconds=300) or \
       limiter.is_rate_limited(ip_key, max_attempts=10, window_seconds=300):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed login attempts. Please try again after 5 minutes."
        )

    user = db.query(User).filter(User.email == req.email.lower()).first()
    if not user or not verify_password(req.password, user.hashed_password):
        limiter.record_attempt(rate_key)
        limiter.record_attempt(ip_key)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been deactivated. Please contact support."
        )

    if not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email address not verified. Please verify your email before logging in."
        )

    # Reset failed rate-limit attempts on successful verification
    limiter.reset(rate_key)

    # Issue JWT and register session in DB
    token, jti, expires_at = create_access_token(
        subject=user.id,
        role=user.role,
        email=user.email
    )
    user_session = UserSession(
        jti=jti,
        user_id=user.id,
        expires_at=expires_at,
        revoked=False
    )
    db.add(user_session)
    db.commit()

    # Issue new session-bound CSRF token
    new_csrf = generate_csrf_token(session_id=jti)

    # Set HttpOnly JWT Cookie
    response.set_cookie(
        key=settings.COOKIE_NAME,
        value=token,
        httponly=True,
        samesite=settings.COOKIE_SAMESITE,
        secure=settings.COOKIE_SECURE,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/"
    )
    # Set Readable Session-Bound CSRF Cookie
    response.set_cookie(
        key=settings.CSRF_COOKIE_NAME,
        value=new_csrf,
        httponly=False,
        samesite=settings.COOKIE_SAMESITE,
        secure=settings.COOKIE_SECURE,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/"
    )

    return user


@router.post(
    "/admin/login",
    response_model=UserSummaryResponse,
    # NOTE: Intentionally NOT guarded by require_legacy_auth_mode.
    # Admin accounts are never linked to Supabase Auth via public endpoints; they
    # always authenticate with their Argon2id password stored in public.users.
    # This endpoint is safe in both AUTH_MODE=legacy and AUTH_MODE=supabase.
    dependencies=[Depends(verify_csrf)],
    summary="Admin Login (Requires Role 'admin')"
)
def admin_login(
    req: UserLoginRequest,
    response: Response,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Dedicated login interface for system administrators.
    Rejects standard users with 403 Forbidden even if credentials match.
    """
    limiter = get_rate_limiter()
    rate_key = f"admin_login:{req.email.lower()}"
    client_ip = request.client.host if request.client else "unknown"
    ip_key = f"admin_login_ip:{client_ip}"

    if limiter.is_rate_limited(rate_key, max_attempts=5, window_seconds=300) or \
       limiter.is_rate_limited(ip_key, max_attempts=10, window_seconds=300):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed administrative login attempts. Locked for 5 minutes."
        )

    user = db.query(User).filter(User.email == req.email.lower()).first()
    if not user or not verify_password(req.password, user.hashed_password):
        limiter.record_attempt(rate_key)
        limiter.record_attempt(ip_key)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid administrative credentials."
        )

    if user.role != "admin":
        limiter.record_attempt(rate_key)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted: This account does not possess administrator privileges."
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative account has been deactivated."
        )

    if not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative email address not verified."
        )

    limiter.reset(rate_key)

    token, jti, expires_at = create_access_token(
        subject=user.id,
        role=user.role,
        email=user.email
    )
    user_session = UserSession(
        jti=jti,
        user_id=user.id,
        expires_at=expires_at,
        revoked=False
    )
    db.add(user_session)
    db.commit()

    new_csrf = generate_csrf_token(session_id=jti)

    response.set_cookie(
        key=settings.COOKIE_NAME,
        value=token,
        httponly=True,
        samesite=settings.COOKIE_SAMESITE,
        secure=settings.COOKIE_SECURE,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/"
    )
    response.set_cookie(
        key=settings.CSRF_COOKIE_NAME,
        value=new_csrf,
        httponly=False,
        samesite=settings.COOKIE_SAMESITE,
        secure=settings.COOKIE_SECURE,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/"
    )

    return user


@router.post(
    "/logout",
    dependencies=[Depends(verify_csrf)],
    summary="User Logout (Revokes Session & Clears Cookies)"
)
def logout_user(
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Revokes the current server-side session in user_sessions, deletes the HttpOnly
    access token cookie, and re-issues an initial guest CSRF token.
    """
    token = extract_token_from_request(request)
    if token:
        payload = decode_access_token(token)
        if payload and payload.get("jti"):
            jti = payload["jti"]
            session_rec = db.query(UserSession).filter(UserSession.jti == jti).first()
            if session_rec:
                session_rec.revoked = True
                session_rec.revoked_at = datetime.utcnow()
                db.commit()

    # Clear HttpOnly access token cookie
    response.delete_cookie(
        key=settings.COOKIE_NAME,
        path="/",
        samesite=settings.COOKIE_SAMESITE,
        secure=settings.COOKIE_SECURE
    )
    # Refresh with fresh guest CSRF token
    guest_csrf = generate_csrf_token(session_id="guest")
    response.set_cookie(
        key=settings.CSRF_COOKIE_NAME,
        value=guest_csrf,
        httponly=False,
        samesite=settings.COOKIE_SAMESITE,
        secure=settings.COOKIE_SECURE,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/"
    )

    return {"message": "Logged out successfully. Session revoked."}


@router.get("/me", response_model=UserSummaryResponse, summary="Get Current User Profile")
def get_user_profile(current_user: User = Depends(get_current_user)):
    """Returns the authenticated user's profile information."""
    return current_user


@router.put(
    "/me",
    response_model=UserSummaryResponse,
    dependencies=[Depends(verify_csrf)],
    summary="Update Profile Information"
)
def update_user_profile(
    req: UserProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Updates user full_name, phone, or address. Role and status cannot be modified here."""
    if req.full_name is not None:
        current_user.full_name = req.full_name
    if req.phone is not None:
        current_user.phone = req.phone
    if req.address is not None:
        current_user.address = req.address

    db.commit()
    db.refresh(current_user)
    return current_user


@router.post(
    "/change-password",
    dependencies=[Depends(require_legacy_auth_mode), Depends(verify_csrf)],
    summary="Change Password (Revokes All Sessions)"
)
def change_password(
    req: ChangePasswordRequest,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Changes the authenticated user's password using Argon2id.
    Revokes all existing active sessions and creates a fresh session for the user.
    """
    if not verify_password(req.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password verification failed."
        )

    is_valid, err_msg = validate_password_strength(req.new_password)
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err_msg)

    # Update password hash
    current_user.hashed_password = get_password_hash(req.new_password)

    # Revoke all existing sessions for this user
    db.query(UserSession).filter(
        UserSession.user_id == current_user.id,
        UserSession.revoked == False
    ).update({"revoked": True, "revoked_at": datetime.utcnow()})

    # Issue a brand new session for current device
    token, jti, expires_at = create_access_token(
        subject=current_user.id,
        role=current_user.role,
        email=current_user.email
    )
    new_session = UserSession(
        jti=jti,
        user_id=current_user.id,
        expires_at=expires_at,
        revoked=False
    )
    db.add(new_session)
    db.commit()

    new_csrf = generate_csrf_token(session_id=jti)
    response.set_cookie(
        key=settings.COOKIE_NAME,
        value=token,
        httponly=True,
        samesite=settings.COOKIE_SAMESITE,
        secure=settings.COOKIE_SECURE,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/"
    )
    response.set_cookie(
        key=settings.CSRF_COOKIE_NAME,
        value=new_csrf,
        httponly=False,
        samesite=settings.COOKIE_SAMESITE,
        secure=settings.COOKIE_SECURE,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/"
    )

    return {"message": "Password changed successfully. All previous sessions have been revoked."}


@router.post(
    "/forgot-password",
    dependencies=[Depends(require_legacy_auth_mode), Depends(verify_csrf)],
    summary="Request Password Reset"
)
def request_password_reset(
    req: ForgotPasswordRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Initiates password reset flow.
    Always returns a uniform generic response regardless of whether the email exists.
    Stores only the SHA-256 hash of a cryptographically secure token.
    Never logs raw reset tokens.
    """
    limiter = get_rate_limiter()
    client_ip = request.client.host if request.client else "unknown"
    rate_key = f"forgot_pw:{client_ip}:{req.email.lower()}"

    if limiter.is_rate_limited(rate_key, max_attempts=3, window_seconds=900):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many password reset requests. Please wait 15 minutes."
        )
    limiter.record_attempt(rate_key)

    user = db.query(User).filter(User.email == req.email.lower()).first()
    if user and user.is_active:
        raw_token = secrets.token_urlsafe(32)
        token_hash = hash_token(raw_token)
        expires_at = datetime.utcnow() + timedelta(minutes=settings.RESET_TOKEN_EXPIRE_MINUTES)

        # Invalidate any existing unused reset tokens for this user
        db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used == False
        ).update({"used": True})

        record = PasswordResetToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
            used=False
        )
        db.add(record)
        db.commit()

        # Build the password reset link.
        # In production: FRONTEND_URL must be set to the real HTTPS frontend origin.
        # In development: falls back to the local dev server URL.
        reset_link = f"{settings.FRONTEND_URL.rstrip('/')}/reset-password?token={raw_token}"

        if settings.SMTP_HOST:
            # Dispatch real email via configured SMTP provider
            try:
                send_password_reset_email(to_email=user.email, reset_link=reset_link)
            except EmailDeliveryError as exc:
                # Log the delivery failure category without exposing raw token or credentials.
                logger.warning(
                    "Password reset email delivery failed for user_id=%s: %s",
                    user.id, str(exc)
                )
                # Continue — the token is stored in DB; the user can retry.
                # Do NOT raise an HTTP error or expose the internal failure.
        else:
            # No SMTP provider configured.
            # In development mode, cache the raw token for test inspection.
            if settings.ENVIRONMENT in ("development", "test"):
                request.app.state.dev_last_reset_token = {
                    "email": user.email,
                    "token": raw_token,
                    "expires_at": expires_at.isoformat()
                }

            else:
                # Production with no SMTP configured: log a warning, continue.
                logger.warning(
                    "SMTP_HOST is not configured. Password reset email was NOT sent "
                    "for user_id=%s. Set SMTP_HOST to enable email delivery.",
                    user.id
                )

    return {
        "message": "If an account with that email exists, password reset instructions have been sent."
    }



@router.get(
    "/dev/last-reset-token",
    dependencies=[Depends(require_legacy_auth_mode)],
    summary="Development-Only Reset Token Inspection"
)
def dev_get_last_reset_token(request: Request, email: str):
    """
    STRICTLY DISABLED IN PRODUCTION (returns 404).
    Permitted only in local development to facilitate automated test suites without requiring SMTP.
    """
    if settings.ENVIRONMENT not in ("development", "test"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Endpoint not found")

    cached = getattr(request.app.state, "dev_last_reset_token", None)
    if not cached or cached.get("email") != email.lower():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active dev reset token found")

    return {"email": cached["email"], "token": cached["token"]}


@router.post(
    "/reset-password",
    dependencies=[Depends(require_legacy_auth_mode), Depends(verify_csrf)],
    summary="Complete Password Reset"
)
def reset_password(req: ResetPasswordRequest, db: Session = Depends(get_db)):
    """
    Validates submitted reset token hash, checks expiration and single-use,
    updates user password with Argon2id, and revokes all active sessions.
    """
    is_valid, err_msg = validate_password_strength(req.new_password)
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err_msg)

    incoming_hash = hash_token(req.token)
    reset_record = db.query(PasswordResetToken).filter(
        PasswordResetToken.token_hash == incoming_hash
    ).first()

    if not reset_record or reset_record.used or reset_record.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid, expired, or already used password reset token."
        )

    user = db.query(User).filter(User.id == reset_record.user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Associated account is inactive or not found."
        )

    # Mark reset token as used (single-use enforcement)
    reset_record.used = True
    user.hashed_password = get_password_hash(req.new_password)

    # Revoke all existing sessions for this user across all devices
    db.query(UserSession).filter(
        UserSession.user_id == user.id,
        UserSession.revoked == False
    ).update({"revoked": True, "revoked_at": datetime.utcnow()})

    db.commit()

    return {
        "message": "Password has been successfully reset. You may now log in with your new password."
    }


@router.post(
    "/provision-profile",
    response_model=UserSummaryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Provision public.users profile for a new Supabase Auth user"
)
def provision_user_profile(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Called after a new user registers via Supabase Auth.
    Requires a valid Supabase JWT (Bearer token). Creates the public.users profile.
    
    Security Controls:
    1. Requires email confirmation (email_confirmed_at or user_metadata.email_verified).
    2. Strictly forbids automatic linking of existing public.users profiles based only on email.
    3. Never allows public registration to claim an existing admin profile or legacy account (409 Conflict).
    4. Hardcodes new profile role to 'user'.
    """
    from app.core.security import decode_supabase_jwt
    from app.core.config import settings as cfg

    if cfg.AUTH_MODE != "supabase":
        raise HTTPException(status_code=404, detail="Endpoint not available in legacy auth mode")

    token = extract_token_from_request(request)
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")

    payload = decode_supabase_jwt(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    auth_uid = payload.get("sub")
    email = payload.get("email", "")
    if not auth_uid or not email:
        raise HTTPException(status_code=401, detail="Malformed token")

    # Email confirmation check
    email_confirmed = bool(
        payload.get("email_confirmed_at") or
        payload.get("user_metadata", {}).get("email_verified") or
        payload.get("app_metadata", {}).get("provider") not in (None, "email")
    )
    if not email_confirmed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email address must be confirmed before provisioning profile."
        )

    # Check if profile already exists for this Supabase user (idempotent)
    existing_by_uid = db.query(User).filter(User.auth_user_id == auth_uid).first()
    if existing_by_uid:
        return existing_by_uid

    # CRITICAL SECURITY RULE: Never auto-link existing public.users by email.
    # Prevents account takeover of existing accounts / admin accounts.
    existing_by_email = db.query(User).filter(User.email == email.lower()).first()
    if existing_by_email:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email address already exists. Automatic account linking is disabled for security. Existing accounts must be linked through the trusted account linking verification process."
        )

    user_metadata = payload.get("user_metadata", {})
    full_name = user_metadata.get("full_name", "") or email.split("@")[0]
    phone = user_metadata.get("phone")
    address = user_metadata.get("address")

    # New profile creation: strictly role='user'
    new_user = User(
        auth_user_id=auth_uid,
        email=email.lower(),
        hashed_password=None,
        full_name=full_name,
        phone=phone,
        address=address,
        role="user",
        email_verified=True,
        is_active=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.post(
    "/link-legacy-account",
    response_model=UserSummaryResponse,
    summary="Securely link an existing legacy account to Supabase Auth"
)
def link_legacy_account(
    req: LinkLegacyAccountRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Secure, one-time trusted account linking for pre-existing legacy accounts.
    Requires:
    1. Valid Supabase JWT with verified email matching the legacy account.
    2. Valid plaintext password verified against stored Argon2id hash.
    3. Admin profiles CANNOT be linked via this public endpoint (must use CLI migration).
    """
    from app.core.security import decode_supabase_jwt, verify_password
    from app.core.config import settings as cfg

    if cfg.AUTH_MODE != "supabase":
        raise HTTPException(status_code=404, detail="Endpoint not available in legacy auth mode")

    token = extract_token_from_request(request)
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")

    payload = decode_supabase_jwt(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    auth_uid = payload.get("sub")
    email = payload.get("email", "")
    if not auth_uid or not email:
        raise HTTPException(status_code=401, detail="Malformed token")

    # Email confirmation check
    email_confirmed = bool(
        payload.get("email_confirmed_at") or
        payload.get("user_metadata", {}).get("email_verified") or
        payload.get("app_metadata", {}).get("provider") not in (None, "email")
    )
    if not email_confirmed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email address must be confirmed before linking accounts."
        )

    # Check if this Supabase user is already linked
    linked_user = db.query(User).filter(User.auth_user_id == auth_uid).first()
    if linked_user:
        return linked_user

    # Find the target legacy user
    legacy_user = db.query(User).filter(User.email == email.lower()).first()
    if not legacy_user:
        raise HTTPException(status_code=404, detail="No existing legacy account found for this email address.")

    if legacy_user.auth_user_id is not None:
        raise HTTPException(status_code=409, detail="This legacy account is already linked to a Supabase authentication user.")

    # CRITICAL: Admin accounts cannot be linked publicly
    if legacy_user.role == "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative accounts cannot be linked via public endpoints. Administrator migration must be performed via administrative tooling."
        )

    # Verify password against legacy Argon2id hash
    if not legacy_user.hashed_password or not verify_password(req.legacy_password, legacy_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Legacy password verification failed. Account linking refused."
        )

    # One-time link and retire legacy password hash
    legacy_user.auth_user_id = auth_uid
    legacy_user.hashed_password = None
    legacy_user.email_verified = True
    
    # Revoke any legacy sessions
    db.query(UserSession).filter(
        UserSession.user_id == legacy_user.id,
        UserSession.revoked == False
    ).update({"revoked": True, "revoked_at": datetime.utcnow()})

    db.commit()
    db.refresh(legacy_user)
    return legacy_user
