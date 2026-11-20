import os
from pathlib import Path
from typing import List, Dict, Optional
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Known weak/default JWT keys that must never be used in production
_KNOWN_WEAK_JWT_KEYS = {
    "roofwise-super-secret-jwt-key-2026-bangladesh-solar-platform-dev-at-least-32-chars",
    "secret",
    "changeme",
    "your-secret-key",
    "jwt-secret",
    "jwt_secret",
}

BASE_DIR = Path(__file__).resolve().parent.parent.parent
# Load local .env file if present
load_dotenv(BASE_DIR / ".env")

class Settings(BaseModel):
    PROJECT_NAME: str = "RoofwiseBD"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    # Environment: Checks ROOFWISE_ENV first, then ENVIRONMENT, defaulting to "development"
    ENVIRONMENT: str = (os.getenv("ROOFWISE_ENV") or os.getenv("ENVIRONMENT") or "development").lower()
    
    # Security & JWT
    JWT_SECRET_KEY: str = os.getenv(
        "JWT_SECRET_KEY", 
        "roofwise-super-secret-jwt-key-2026-bangladesh-solar-platform-dev-at-least-32-chars"
    )
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

    # Supabase Auth Integration
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "")
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    SUPABASE_JWT_SECRET: str = os.getenv("SUPABASE_JWT_SECRET", "")
    # Auth mode: "supabase" = verify Supabase JWTs; "legacy" = old custom HS256 JWT
    AUTH_MODE: str = os.getenv("AUTH_MODE", "legacy")

    # Cookie & CSRF Settings
    COOKIE_NAME: str = "roofwise_access_token"
    CSRF_COOKIE_NAME: str = "roofwise_csrf_token"
    COOKIE_SECURE: bool = os.getenv("COOKIE_SECURE", "false").lower() == "true"
    COOKIE_SAMESITE: str = os.getenv("COOKIE_SAMESITE", "lax").lower()
    
    # CORS (Configurable via comma-separated BACKEND_CORS_ORIGINS env var or regex)
    BACKEND_CORS_ORIGINS: List[str] = [
        origin.strip() for origin in os.getenv(
            "BACKEND_CORS_ORIGINS", 
            "http://127.0.0.1:5173,http://localhost:5173,http://127.0.0.1:8000,http://localhost:8000"
        ).split(",") if origin.strip()
    ]
    BACKEND_CORS_ORIGIN_REGEX: Optional[str] = os.getenv("BACKEND_CORS_ORIGIN_REGEX", None)
    
    # Rate Limiting & Production Cache Interface
    REDIS_URL: str = os.getenv("REDIS_URL", "")
    
    # Rate Limiter Failure Policy during Redis Downtime:
    #   "strict_quota"    — (Recommended default) Falls back to local in-memory, but divides allowed
    #                       attempts by RATE_LIMIT_ESTIMATED_WORKERS to prevent multi-worker multiplier attacks.
    #   "fail_closed"     — Rejects/throttles sensitive requests immediately when Redis is unreachable.
    #   "fallback_memory" — Falls back to unscaled worker-local in-memory rate limiting.
    RATE_LIMIT_FAILURE_POLICY: str = os.getenv("RATE_LIMIT_FAILURE_POLICY", "strict_quota")
    RATE_LIMIT_ESTIMATED_WORKERS: int = int(os.getenv("RATE_LIMIT_ESTIMATED_WORKERS", "4"))

    
    # Password Reset & Email Delivery Provider
    RESET_TOKEN_EXPIRE_MINUTES: int = 15
    SMTP_HOST: str = os.getenv("SMTP_HOST", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    EMAIL_FROM: str = os.getenv("EMAIL_FROM", "noreply@roofwisebd.com")

    # Frontend URL for constructing password reset links
    # Production: must be set to the real HTTPS frontend origin (e.g. https://roofwisebd.com)
    # Development: defaults to local Vite dev server
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://127.0.0.1:5173")
    
    # Storage Paths
    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    DATA_DIR: Path = BASE_DIR.parent / "data"
    MODELS_DIR: Path = BASE_DIR.parent / "models"
    DATABASE_URL: str = Field(default_factory=lambda: os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/roofwise.db"))
    
    # SREDA Net Metering Guideline 2025 Compliance
    # Guideline rule: Renewable Energy Converter AC output capacity must NOT exceed sanctioned load.
    MAX_AC_TO_SANCTIONED_RATIO: float = 1.00  # Inverter AC kW <= Sanctioned Load kW
    THREE_PHASE_THRESHOLD_KW: float = 10.0   # > 10 kW generally mandates 3-phase utility infrastructure
    
    # Solar Module Reference Specifications (Configurable)
    DEFAULT_PANEL_WATTAGE_WP: int = 550
    DEFAULT_PANEL_AREA_SQFT: float = 27.2
    DEFAULT_SQFT_PER_KWP: float = 85.0
    DEFAULT_TIN_SQFT_PER_KWP: float = 75.0
    DEFAULT_TILT_DEGREE: float = 23.0  # Configurable 22-24° south-facing reference for BD
    DEFAULT_INVERTER_DC_AC_RATIO: float = 1.20  # Standard DC oversizing ratio
    DEFAULT_SYSTEM_PR: float = 0.78  # System performance ratio (dust, wiring, temperature losses)
    
    # Location- and Month-Specific Monthly Solar Irradiance Baseline (kWh/m²/day)
    # Source: NASA POWER Agroclimatology monthly multi-year averages for Bangladesh divisions
    DIVISION_MONTHLY_PSH: Dict[str, List[float]] = {
        "Dhaka": [4.15, 4.85, 5.50, 5.80, 5.40, 4.30, 4.10, 4.20, 4.35, 4.70, 4.40, 4.05],
        "Chattogram": [4.30, 5.00, 5.65, 5.95, 5.25, 3.90, 3.80, 3.95, 4.25, 4.65, 4.50, 4.20],
        "Rajshahi": [4.10, 4.90, 5.70, 6.10, 5.80, 4.60, 4.25, 4.30, 4.45, 4.80, 4.45, 4.00],
        "Khulna": [4.20, 4.95, 5.60, 5.90, 5.50, 4.20, 4.00, 4.10, 4.30, 4.75, 4.45, 4.10],
        "Barishal": [4.25, 5.00, 5.60, 5.85, 5.30, 4.05, 3.95, 4.05, 4.25, 4.65, 4.40, 4.15],
        "Sylhet": [4.05, 4.65, 5.15, 5.35, 4.80, 3.75, 3.70, 3.85, 4.05, 4.45, 4.25, 3.95],
        "Rangpur": [3.95, 4.75, 5.55, 5.90, 5.50, 4.40, 4.10, 4.15, 4.35, 4.70, 4.35, 3.90],
        "Mymensingh": [4.05, 4.80, 5.45, 5.75, 5.25, 4.20, 4.00, 4.10, 4.30, 4.65, 4.35, 3.95],
    }
    
    # Financial Reference Ranges (BDT / kWp Turnkey On-Grid Estimates)
    ESTIMATED_COST_PER_KWP_MIN_BDT: float = 68000.0
    ESTIMATED_COST_PER_KWP_MAX_BDT: float = 85000.0
    HYBRID_BATTERY_ADDON_PER_KWH_BDT: float = 38000.0  # LiFePO4 with BMS
    LEAD_ACID_ADDON_PER_KWH_BDT: float = 18000.0      # Tubular deep-cycle
    
    # Standard Disclaimers
    STRUCTURAL_DISCLAIMER: str = (
        "Roof area analysis and visual inspection provide preliminary spatial sizing only. "
        "A formal structural civil engineering assessment is mandatory prior to physical installation."
    )
    SREDA_ADVISORY: str = (
        "In accordance with Bangladesh Net Metering Guideline 2025, the inverter AC capacity must not "
        "exceed the customer's sanctioned load. Systems exceeding 10 kW require three-phase grid connection "
        "and distribution utility (DESCO/DPDC/BPDB/NESCO/BREB) sanction verification."
    )

    def validate_production_settings(self) -> None:
        """
        Enforces mandatory security requirements when ENVIRONMENT=production.
        Raises RuntimeError with an actionable message if any check fails.
        This prevents the application from starting with insecure development defaults.
        Called at startup in main.py.
        """
        if self.ENVIRONMENT != "production":
            return  # No enforcement in development or test

        errors: list[str] = []

        # 1. JWT secret key must not be a known weak/default value
        if self.JWT_SECRET_KEY in _KNOWN_WEAK_JWT_KEYS:
            errors.append(
                "JWT_SECRET_KEY is set to a known development default. "
                "Generate a strong random secret: "
                "python -c \"import secrets; print(secrets.token_hex(64))\""
            )

        # 2. JWT secret key must be sufficiently long (min 32 chars)
        if len(self.JWT_SECRET_KEY) < 32:
            errors.append(
                f"JWT_SECRET_KEY is too short ({len(self.JWT_SECRET_KEY)} chars). "
                "Production secrets must be at least 32 characters."
            )

        # 3. Cookies must be Secure in production (HTTPS only)
        if not self.COOKIE_SECURE:
            errors.append(
                "COOKIE_SECURE is False. Set COOKIE_SECURE=true to ensure "
                "JWT session cookies are only transmitted over HTTPS."
            )

        # 4. CORS origins must be explicitly configured and safe for production
        disallowed_origins: list[str] = []
        for origin in self.BACKEND_CORS_ORIGINS:
            origin_lower = origin.lower()
            # Reject wildcard
            if origin_lower == "*":
                disallowed_origins.append(f"'{origin}' (wildcard — forbidden with credentials)")
                continue
            # Reject localhost / 127.0.0.1 / 0.0.0.0
            if any(h in origin_lower for h in ("localhost", "127.0.0.1", "0.0.0.0", "::1")):
                disallowed_origins.append(f"'{origin}' (localhost/loopback — not permitted in production)")
                continue
            # Reject non-HTTPS origins
            if not origin_lower.startswith("https://"):
                disallowed_origins.append(f"'{origin}' (non-HTTPS — must use https:// in production)")

        if disallowed_origins:
            joined = ", ".join(disallowed_origins)
            errors.append(
                f"BACKEND_CORS_ORIGINS contains disallowed origins: {joined}. "
                "Production CORS must list only explicit HTTPS domains."
            )

        # 5. At least one CORS origin must be configured
        if not self.BACKEND_CORS_ORIGINS:
            errors.append(
                "BACKEND_CORS_ORIGINS is empty. "
                "Set it to your production frontend URL, e.g. https://roofwisebd.com"
            )

        # 6. SMTP configuration required in production for password reset account recovery
        if not self.SMTP_HOST and os.getenv("ALLOW_INSECURE_NO_SMTP", "false").lower() != "true":
            errors.append(
                "SMTP_HOST is not configured. Production requires a functional "
                "email delivery provider for secure account recovery (password reset). "
                "Set SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, and EMAIL_FROM in your environment. "
                "(Set ALLOW_INSECURE_NO_SMTP=true only if temporarily bypassing for staging testing)."
            )

        # 7. Supabase config required when AUTH_MODE=supabase
        if self.AUTH_MODE == "supabase" and not self.SUPABASE_URL:
            errors.append(
                "AUTH_MODE=supabase but SUPABASE_URL is not set. "
                "Set SUPABASE_URL and SUPABASE_JWT_SECRET from your Supabase dashboard."
            )
        if self.AUTH_MODE == "supabase" and not self.SUPABASE_JWT_SECRET:
            errors.append(
                "AUTH_MODE=supabase but SUPABASE_JWT_SECRET is not set. "
                "Get this from Supabase Dashboard > Settings > API > JWT Secret."
            )

        if errors:
            formatted = "\n  ".join(f"[{i+1}] {e}" for i, e in enumerate(errors))
            raise RuntimeError(
                f"\n\n{'='*70}\n"
                f"PRODUCTION SECURITY CONFIGURATION ERROR — Server startup aborted.\n"
                f"{'='*70}\n"
                f"The following required production settings are missing or insecure:\n\n"
                f"  {formatted}\n\n"
                f"Set these values via environment variables before starting in production.\n"
                f"{'='*70}\n"
            )


settings = Settings()

# Ensure uploads folder exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

