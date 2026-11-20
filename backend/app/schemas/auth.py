import re
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, field_validator
from app.core.validation import (
    validate_full_name,
    validate_bangladesh_phone,
    validate_bangladesh_district,
    validate_email_format,
)

class UserRegisterRequest(BaseModel):
    """
    User registration payload.
    Role is intentionally omitted and strictly hardcoded to 'user' on the backend.
    """
    email: str = Field(..., min_length=3, max_length=254)
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str = Field(..., min_length=2, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = Field(None, max_length=255)

    @field_validator("full_name")
    @classmethod
    def check_full_name(cls, v: str) -> str:
        is_valid, msg = validate_full_name(v)
        if not is_valid:
            raise ValueError(msg)
        return v.strip()

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        raw = str(v).strip()
        is_valid, msg = validate_email_format(raw)
        if not is_valid:
            raise ValueError(msg)
        return raw.lower()

    @field_validator("phone")
    @classmethod
    def check_phone(cls, v: Optional[str]) -> Optional[str]:
        is_valid, norm, msg = validate_bangladesh_phone(v)
        if not is_valid:
            raise ValueError(msg)
        return norm

    @field_validator("address")
    @classmethod
    def check_district(cls, v: Optional[str]) -> Optional[str]:
        is_valid, norm, msg = validate_bangladesh_district(v)
        if not is_valid:
            raise ValueError(msg)
        return norm

class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)

class UserSummaryResponse(BaseModel):
    id: int
    email: str
    full_name: str
    phone: Optional[str] = None
    address: Optional[str] = None
    role: str
    is_active: bool
    email_verified: bool = False
    created_at: datetime
    auth_user_id: Optional[str] = None

    class Config:
        from_attributes = True

class VerifyEmailRequest(BaseModel):
    email: str = Field(..., max_length=254)
    otp: str = Field(..., min_length=6, max_length=6)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return str(v).strip().lower()

    @field_validator("otp")
    @classmethod
    def validate_otp(cls, v: str) -> str:
        cleaned = str(v).strip()
        if not re.match(r"^\d{6}$", cleaned):
            raise ValueError("Verification code must be exactly 6 digits.")
        return cleaned

class ResendVerificationRequest(BaseModel):
    email: str = Field(..., max_length=254)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return str(v).strip().lower()

class UserProfileUpdateRequest(BaseModel):
    """Profile update payload. Role and status cannot be modified here."""
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = Field(None, max_length=255)

class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=1, max_length=128)
    new_password: str = Field(..., min_length=8, max_length=128)

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=128)

class LinkLegacyAccountRequest(BaseModel):
    """Payload for verifying and securely linking a legacy account to Supabase Auth."""
    legacy_password: str = Field(..., min_length=1, max_length=128, description="Existing account password from custom auth")


class ClaimAssessmentRequest(BaseModel):
    claim_token: str = Field(..., min_length=1)

class AdminUserItem(BaseModel):
    id: int
    email: str
    full_name: str
    phone: Optional[str] = None
    address: Optional[str] = None
    role: str
    is_active: bool
    email_verified: bool = True
    created_at: datetime
    assessment_count: int = 0

    class Config:
        from_attributes = True

class AdminToggleUserStatusRequest(BaseModel):
    is_active: bool

class AdminStatsResponse(BaseModel):
    total_users: int
    active_users: int
    total_assessments: int
    guest_assessments: int
    user_assessments: int
    total_capacity_kwp: float
    total_monthly_savings_bdt: float

class CSRFResponse(BaseModel):
    csrf_token: str
