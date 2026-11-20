import re
import hmac
import uuid
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, Any
import jwt
from pwdlib import PasswordHash
from app.core.config import settings

from jwt import PyJWKClient, PyJWKClientError

# Initialize Argon2id password hasher via pwdlib recommended defaults
_pwd_context = PasswordHash.recommended()

def get_password_hash(password: str) -> str:
    """Hash plaintext password using Argon2id."""
    return _pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plaintext password against stored Argon2id hash."""
    try:
        return _pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False

def validate_password_strength(password: str) -> Tuple[bool, str]:
    """
    Validate password strength according to security requirements:
    - Minimum 8 characters, maximum 128 characters (prevents hashing DoS).
    - Requires at least one letter.
    - Requires at least one digit.
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if len(password) > 128:
        return False, "Password cannot exceed 128 characters."
    if not re.search(r"[A-Za-z]", password):
        return False, "Password must contain at least one letter."
    if not re.search(r"\d", password):
        return False, "Password must contain at least one number."
    return True, ""

def create_access_token(
    subject: int,
    role: str,
    email: str,
    expires_delta: Optional[timedelta] = None
) -> Tuple[str, str, datetime]:
    """
    Creates a signed HS256 JWT access token with a unique jti identifier.
    Returns: (token_str, jti, expires_at_datetime)
    """
    now = datetime.utcnow()
    expires_at = now + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    jti = uuid.uuid4().hex
    
    payload: Dict[str, Any] = {
        "sub": str(subject),
        "email": email,
        "role": role,
        "jti": jti,
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp())
    }
    
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token, jti, expires_at

def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decodes and validates a JWT token. Returns payload dict or None if invalid/expired."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except jwt.PyJWTError:
        return None

def hash_token(raw_token: str) -> str:
    """Computes a SHA-256 hex digest of a token (e.g. claim secrets or reset tokens)."""
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

def generate_numeric_otp(digits: int = 6) -> str:
    """Generates a cryptographically secure numeric OTP."""
    num = secrets.randbelow(10 ** digits)
    return f"{num:0{digits}d}"

def hash_otp(raw_otp: str, user_id: int) -> str:
    """Computes a keyed HMAC-SHA256 hash of a numeric OTP bound to user_id."""
    payload = f"{user_id}:{raw_otp}".encode("utf-8")
    return hmac.new(settings.JWT_SECRET_KEY.encode("utf-8"), payload, hashlib.sha256).hexdigest()

def verify_otp_hash(raw_otp: str, user_id: int, stored_hash: str) -> bool:
    """Constant-time verification of OTP hash against stored HMAC-SHA256."""
    if not raw_otp or not stored_hash:
        return False
    expected_hash = hash_otp(raw_otp, user_id)
    return secrets.compare_digest(expected_hash, stored_hash)

def secure_compare(a: str, b: str) -> bool:
    """Constant-time string comparison to prevent timing attacks."""
    if not a or not b:
        return False
    return secrets.compare_digest(a, b)

def generate_csrf_token(session_id: str = "guest") -> str:
    """
    Generates a cryptographically signed, session-bound CSRF token.
    Token format: {nonce}.{hmac_signature(nonce + session_id)}
    """
    nonce = secrets.token_hex(16)
    sig_payload = f"{nonce}:{session_id}".encode("utf-8")
    signature = hmac.new(
        settings.JWT_SECRET_KEY.encode("utf-8"),
        sig_payload,
        hashlib.sha256
    ).hexdigest()
    return f"{nonce}.{signature}"

def verify_csrf_token(csrf_token: str, session_id: str = "guest") -> bool:
    """Verifies that a CSRF token matches the session_id and has a valid HMAC signature."""
    try:
        if not csrf_token or "." not in csrf_token:
            return False
        parts = csrf_token.split(".")
        if len(parts) != 2:
            return False
        nonce, received_sig = parts
        sig_payload = f"{nonce}:{session_id}".encode("utf-8")
        expected_sig = hmac.new(
            settings.JWT_SECRET_KEY.encode("utf-8"),
            sig_payload,
            hashlib.sha256
        ).hexdigest()
        return secrets.compare_digest(received_sig, expected_sig)
    except Exception:
        return False


# JWKS Client cache for asymmetric Supabase JWT verification
_jwks_client: Optional[PyJWKClient] = None
_jwks_client_url: Optional[str] = None


def get_jwks_client(custom_url: Optional[str] = None) -> Optional[PyJWKClient]:
    """
    Returns a cached PyJWKClient configured with a maximum 300-second lifespan
    for asymmetric key discovery and automatic key rotation.
    """
    global _jwks_client, _jwks_client_url
    if _jwks_client is not None and not custom_url:
        return _jwks_client

    target_url = custom_url or (
        f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/.well-known/jwks.json"
        if settings.SUPABASE_URL else None
    )
    if not target_url:
        return None

    if _jwks_client is None or _jwks_client_url != target_url:
        _jwks_client_url = target_url
        _jwks_client = PyJWKClient(
            target_url,
            cache_jwk_set=True,
            lifespan=300  # Enforce 300s max application cache per security architecture
        )
    return _jwks_client


def set_jwks_client_for_testing(client: Optional[PyJWKClient]) -> None:
    """Allows test fixtures to inject an in-memory/mock JWKS client."""
    global _jwks_client, _jwks_client_url
    _jwks_client = client
    _jwks_client_url = "test://mock-jwks" if client else None


def decode_supabase_jwt(token: str) -> Optional[Dict[str, Any]]:
    """
    Decodes and verifies a Supabase-issued access token.
    
    Security design:
    1. Inspects the unverified JWT header to determine the active signing algorithm.
    2. If asymmetric (e.g. ES256, RS256) or if 'kid' is present, verifies against
       Supabase's JWKS endpoint via PyJWKClient with a 300-second cache. Automatic
       key rotation is handled when a new 'kid' is presented.
    3. If symmetric (HS256) and SUPABASE_JWT_SECRET is configured, verifies using
       the shared secret.
    4. Validates audience ("authenticated") and standard expiration (exp).
    
    Returns payload dictionary or None if verification fails.
    """
    if not token or not isinstance(token, str):
        return None

    try:
        header = jwt.get_unverified_header(token)
    except Exception:
        return None

    alg = header.get("alg")
    kid = header.get("kid")

    # 1. Asymmetric verification via JWKS (preferred for Supabase projects using ES256 / RS256)
    if kid or alg in ("ES256", "RS256", "EdDSA"):
        jwks_client = get_jwks_client()
        if jwks_client:
            try:
                signing_key = jwks_client.get_signing_key_from_jwt(token)
                payload = jwt.decode(
                    token,
                    signing_key.key,
                    algorithms=[alg] if alg else ["ES256", "RS256"],
                    audience="authenticated"
                )
                return payload
            except (PyJWKClientError, jwt.PyJWTError):
                pass

    # 2. Symmetric verification fallback (HS256)
    if alg == "HS256" and settings.SUPABASE_JWT_SECRET:
        try:
            payload = jwt.decode(
                token,
                settings.SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
                audience="authenticated"
            )
            return payload
        except jwt.PyJWTError:
            pass

    return None
