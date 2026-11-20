from datetime import datetime
from sqlalchemy import Column, Integer, Float, String, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.database.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    auth_user_id = Column(String(36), unique=True, nullable=True, index=True)
    hashed_password = Column(String(255), nullable=True)
    full_name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=True)
    address = Column(String(255), nullable=True)
    role = Column(String(20), default="user", nullable=False)  # "user" or "admin"
    is_active = Column(Boolean, default=True, nullable=False)
    email_verified = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    assessments = relationship("AssessmentRecord", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    reset_tokens = relationship("PasswordResetToken", back_populates="user", cascade="all, delete-orphan")
    verification_otps = relationship("EmailVerificationOTP", back_populates="user", cascade="all, delete-orphan")


class UserSession(Base):
    """Server-side JWT session revocation and token registry."""
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, index=True)
    jti = Column(String(64), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, index=True, nullable=False)
    revoked = Column(Boolean, default=False, nullable=False)
    revoked_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="sessions")


class PasswordResetToken(Base):
    """Cryptographically secure, single-use password reset tokens stored as SHA-256 hashes."""
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    token_hash = Column(String(64), unique=True, index=True, nullable=False)
    expires_at = Column(DateTime, index=True, nullable=False)
    used = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="reset_tokens")


class EmailVerificationOTP(Base):
    """
    Cryptographically secure, single-use 6-digit email verification OTPs.
    Only the HMAC-SHA256 hash is stored, never plaintext.
    """
    __tablename__ = "email_verification_otps"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    otp_hash = Column(String(64), index=True, nullable=False)
    expires_at = Column(DateTime, index=True, nullable=False)
    used = Column(Boolean, default=False, nullable=False)
    attempts = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="verification_otps")


class AssessmentRecord(Base):
    __tablename__ = "assessments"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # User linkage and secure guest claim token
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    claim_token_hash = Column(String(64), nullable=True, index=True)  # SHA-256 hash of raw claim secret
    
    # Location
    division = Column(String(50), nullable=False)
    district = Column(String(50), nullable=False)
    area = Column(String(100), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    
    # Consumption
    monthly_units_kwh = Column(Float, nullable=False)
    billing_period_days = Column(Integer, default=30)
    bill_amount_bdt = Column(Float, nullable=True)
    sanctioned_load_kw = Column(Float, default=2.0)
    consumer_category = Column(String(50), default="Residential")
    
    # Rooftop
    total_area_sqft = Column(Float, nullable=False)
    usable_area_sqft = Column(Float, nullable=False)
    roof_type = Column(String(50), default="concrete_flat")
    shading_condition = Column(String(50), default="low")
    orientation = Column(String(50), default="South")
    tilt_degrees = Column(Float, default=23.0)
    bill_file_path = Column(String(255), nullable=True)
    
    # Calculation & Sizing Results
    recommended_capacity_kwp = Column(Float, nullable=False)
    recommended_inverter_ac_kw = Column(Float, nullable=False)
    panel_count = Column(Integer, nullable=False)
    daily_generation_kwh = Column(Float, nullable=False)
    monthly_generation_kwh = Column(Float, nullable=False)
    annual_generation_kwh = Column(Float, nullable=False)
    monthly_savings_bdt = Column(Float, nullable=False)
    estimated_payback_years = Column(Float, nullable=False)
    sreda_compliant = Column(Boolean, default=True)
    
    notes = Column(Text, nullable=True)

    user = relationship("User", back_populates="assessments")
