from datetime import datetime
from typing import Optional
from fastapi import Request, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.security import decode_access_token, verify_csrf_token, decode_supabase_jwt
from app.database.database import get_db
from app.database.models import User, UserSession

def extract_token_from_request(request: Request) -> Optional[str]:
    """
    Extracts access token from Authorization Bearer header or HttpOnly cookie.
    Authorization header takes precedence over ambient cookies.
    """
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header[7:].strip()
    return request.cookies.get(settings.COOKIE_NAME)

def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> User:
    """
    Validates JWT token against the server-side user_sessions revocation registry.
    Ensures the account exists and is actively enabled.
    Supports both legacy HS256 JWT mode and Supabase JWT mode (AUTH_MODE env var).
    In Supabase mode, also supports legacy cookie sessions for administrator logins.
    """
    token = extract_token_from_request(request)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    if settings.AUTH_MODE == "supabase":
        payload = decode_supabase_jwt(token)
        if payload and payload.get("sub"):
            auth_uid = payload["sub"]
            user = db.query(User).filter(User.auth_user_id == auth_uid).first()
            if not user:
                raise HTTPException(status_code=401, detail="User profile not found. Registration may be incomplete.")
            if not user.is_active:
                raise HTTPException(status_code=403, detail="Account has been deactivated")
            request.state.current_user = user
            request.state.current_jti = auth_uid  # Use auth_uid as session identifier in Supabase mode
            return user

        # Administrator fallback in Supabase mode:
        # Administrators authenticate via /admin/login using Argon2id and receive
        # a server-side session registry token in an HttpOnly cookie.
        legacy_payload = decode_access_token(token)
        if legacy_payload and legacy_payload.get("sub") and legacy_payload.get("jti"):
            try:
                user_id = int(legacy_payload["sub"])
                jti = legacy_payload["jti"]
                session = db.query(UserSession).filter(UserSession.jti == jti).first()
                if session and not session.revoked and session.expires_at >= datetime.utcnow():
                    admin_user = db.query(User).filter(User.id == user_id).first()
                    if admin_user and admin_user.is_active and admin_user.role == "admin":
                        request.state.current_user = admin_user
                        request.state.current_jti = jti
                        return admin_user
            except (ValueError, TypeError):
                pass

        raise HTTPException(status_code=401, detail="Invalid or expired access token")
    else:
        # Legacy path: existing custom HS256 JWT with server-side session registry
        payload = decode_access_token(token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired access token"
            )

        user_id_str = payload.get("sub")
        jti = payload.get("jti")
        if not user_id_str or not jti:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Malformed token payload"
            )

        try:
            user_id = int(user_id_str)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user subject in token"
            )

        # Server-side session verification
        session = db.query(UserSession).filter(UserSession.jti == jti).first()
        if not session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session not found or expired"
            )
        if session.revoked or session.expires_at < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session has been revoked or expired"
            )

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account no longer exists"
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account has been deactivated"
            )

        # Attach current user and session identifier to request state
        request.state.current_user = user
        request.state.current_jti = jti

        return user

def get_optional_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Optional authentication for endpoints that support both guest and logged-in visitors.
    Returns User if valid session exists, otherwise None without raising HTTP error.
    Supports both legacy and Supabase auth modes.
    """
    token = extract_token_from_request(request)
    if not token:
        return None

    if settings.AUTH_MODE == "supabase":
        payload = decode_supabase_jwt(token)
        if payload and payload.get("sub"):
            auth_uid = payload["sub"]
            user = db.query(User).filter(User.auth_user_id == auth_uid).first()
            if not user or not user.is_active:
                return None
            request.state.current_user = user
            request.state.current_jti = auth_uid  # Use auth_uid as session identifier in Supabase mode
            return user

        # Administrator fallback in Supabase mode
        legacy_payload = decode_access_token(token)
        if legacy_payload and legacy_payload.get("sub") and legacy_payload.get("jti"):
            try:
                user_id = int(legacy_payload["sub"])
                jti = legacy_payload["jti"]
                session = db.query(UserSession).filter(UserSession.jti == jti).first()
                if session and not session.revoked and session.expires_at >= datetime.utcnow():
                    admin_user = db.query(User).filter(User.id == user_id).first()
                    if admin_user and admin_user.is_active and admin_user.role == "admin":
                        request.state.current_user = admin_user
                        request.state.current_jti = jti
                        return admin_user
            except (ValueError, TypeError):
                pass
        return None
    else:
        # Legacy path
        payload = decode_access_token(token)
        if not payload:
            return None

        user_id_str = payload.get("sub")
        jti = payload.get("jti")
        if not user_id_str or not jti:
            return None

        try:
            user_id = int(user_id_str)
        except ValueError:
            return None

        session = db.query(UserSession).filter(UserSession.jti == jti).first()
        if not session or session.revoked or session.expires_at < datetime.utcnow():
            return None

        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            return None

        request.state.current_user = user
        request.state.current_jti = jti
        return user

def get_current_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """Enforces administrator role authorization on backend endpoints."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative privileges required"
        )
    return current_user

def verify_csrf(request: Request) -> None:
    """
    Validates CSRF protection for state-changing requests (POST, PUT, DELETE, PATCH).
    Checks double-submit token match and validates HMAC cryptographic signature.
    Safe methods (GET, HEAD, OPTIONS) are exempt.

    CSRF protection is NOT required for Bearer token authentication:
    browsers cannot send custom Authorization headers cross-origin without
    explicit CORS permission, making Bearer tokens inherently CSRF-safe.
    """
    if request.method not in ["POST", "PUT", "DELETE", "PATCH"]:
        return

    # Bearer token requests are inherently CSRF-safe — skip cookie-based CSRF check
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return

    csrf_header = request.headers.get("X-CSRF-Token")
    csrf_cookie = request.cookies.get(settings.CSRF_COOKIE_NAME)

    if not csrf_header or not csrf_cookie:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF validation failed: missing CSRF token in header or cookie"
        )

    if csrf_header != csrf_cookie:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF validation failed: token mismatch"
        )

    # Determine session ID: either authenticated jti or 'guest'
    session_id = "guest"
    if hasattr(request.state, "current_jti") and request.state.current_jti:
        session_id = request.state.current_jti
    else:
        # Check if an access token is in cookie to resolve jti
        token = extract_token_from_request(request)
        if token:
            payload = decode_access_token(token)
            if payload and payload.get("jti"):
                session_id = payload["jti"]

    if not verify_csrf_token(csrf_header, session_id):
        # Also allow guest signature if user was in transition
        if not verify_csrf_token(csrf_header, "guest"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CSRF validation failed: invalid cryptographic signature"
            )
