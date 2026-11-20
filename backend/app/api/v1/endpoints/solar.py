import secrets
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.database.models import AssessmentRecord, User
from app.schemas.recommendation import SolarRecommendationRequest, SolarRecommendationResponse
from app.schemas.assessment import (
    SolarAssessmentRequest,
    SolarAssessmentResponse,
    LocationInfo,
    ConsumptionInfo,
    RooftopInfo
)
from app.schemas.auth import ClaimAssessmentRequest
from app.services.solar_recommendation_service import generate_solar_recommendations
from app.core.security import hash_token, secure_compare
from app.api.deps import (
    get_current_user,
    get_optional_current_user,
    verify_csrf
)

router = APIRouter()

@router.post(
    "/solar/recommendation",
    response_model=SolarRecommendationResponse,
    summary="Generate Solar System Recommendation"
)
def get_solar_recommendation(req: SolarRecommendationRequest):
    return generate_solar_recommendations(req)


@router.post(
    "/solar/assessment",
    response_model=SolarAssessmentResponse,
    summary="Submit Full Solar Assessment (Guest or Authenticated)"
)
def submit_solar_assessment(
    req: SolarAssessmentRequest,
    db: Session = Depends(get_db),
    optional_user: Optional[User] = Depends(get_optional_current_user)
):
    """
    Submits a solar assessment.
    - If user is authenticated: Automatically binds assessment to user_id.
    - If user is a guest: Generates a cryptographically secure 32-byte claim token,
      stores only its SHA-256 hash in SQLite, and returns the raw claim token ONCE in the response.
    """
    # 1. Run recommendation calculation
    rec = generate_solar_recommendations(SolarRecommendationRequest(
        monthly_units_kwh=req.consumption.monthly_units_kwh,
        total_roof_area_sqft=req.rooftop.total_area_sqft,
        sanctioned_load_kw=req.consumption.sanctioned_load_kw,
        division=req.location.division,
        roof_type=req.rooftop.roof_type,
        shading_condition=req.rooftop.shading_condition,
        usable_roof_area_sqft=req.rooftop.usable_area_sqft
    ))

    tier = rec.recommended_system

    raw_claim_token = None
    claim_token_hash = None
    user_id = None
    is_guest = True

    if optional_user:
        user_id = optional_user.id
        is_guest = False
    else:
        # Generate one-time secure claim token for guest
        raw_claim_token = secrets.token_urlsafe(32)
        claim_token_hash = hash_token(raw_claim_token)

    # 2. Persist to SQLite Database
    record = AssessmentRecord(
        created_at=datetime.utcnow(),
        user_id=user_id,
        claim_token_hash=claim_token_hash,
        division=req.location.division,
        district=req.location.district,
        area=req.location.area,
        latitude=req.location.latitude,
        longitude=req.location.longitude,
        monthly_units_kwh=req.consumption.monthly_units_kwh,
        billing_period_days=req.consumption.billing_period_days,
        bill_amount_bdt=req.consumption.bill_amount_bdt,
        sanctioned_load_kw=req.consumption.sanctioned_load_kw,
        consumer_category=req.consumption.consumer_category,
        total_area_sqft=req.rooftop.total_area_sqft,
        usable_area_sqft=tier.required_usable_area_sqft,
        roof_type=req.rooftop.roof_type,
        shading_condition=req.rooftop.shading_condition,
        orientation=req.rooftop.orientation or "South",
        tilt_degrees=req.rooftop.tilt_degrees or 23.0,
        bill_file_path=req.bill_file_path,
        recommended_capacity_kwp=tier.dc_capacity_kwp,
        recommended_inverter_ac_kw=tier.inverter_ac_kw,
        panel_count=tier.panel_count,
        daily_generation_kwh=tier.daily_generation_kwh,
        monthly_generation_kwh=tier.monthly_generation_kwh,
        annual_generation_kwh=tier.annual_generation_kwh,
        monthly_savings_bdt=tier.est_monthly_savings_bdt,
        estimated_payback_years=tier.est_payback_years_min,
        sreda_compliant=rec.sreda_compliance.is_compliant,
        notes=req.notes
    )

    db.add(record)
    db.commit()
    db.refresh(record)

    return SolarAssessmentResponse(
        id=record.id,
        created_at=record.created_at.isoformat(),
        location=req.location,
        consumption=req.consumption,
        rooftop=req.rooftop,
        recommended_capacity_kwp=tier.dc_capacity_kwp,
        recommended_inverter_ac_kw=tier.inverter_ac_kw,
        panel_count=tier.panel_count,
        daily_generation_kwh=tier.daily_generation_kwh,
        monthly_generation_kwh=tier.monthly_generation_kwh,
        annual_generation_kwh=tier.annual_generation_kwh,
        monthly_savings_bdt=tier.est_monthly_savings_bdt,
        estimated_payback_years=tier.est_payback_years_min,
        sreda_compliant=rec.sreda_compliance.is_compliant,
        sreda_advisory=rec.sreda_compliance.advisory_text,
        structural_disclaimer=rec.disclaimer,
        claim_token=raw_claim_token,
        is_guest=is_guest
    )


@router.get("/solar/user/assessments", summary="Get Current User's Saved Assessments")
def get_user_assessments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns only assessments belonging to the authenticated user.
    Strict tenant isolation prevents accessing other users' assessments.
    """
    records = db.query(AssessmentRecord).filter(
        AssessmentRecord.user_id == current_user.id
    ).order_by(AssessmentRecord.id.desc()).all()

    return records


@router.get("/solar/assessment/{assessment_id}", summary="Get Single Assessment Details")
def get_single_assessment(
    assessment_id: int,
    request: Request,
    db: Session = Depends(get_db),
    optional_user: Optional[User] = Depends(get_optional_current_user)
):
    """
    Retrieves assessment details with authorization checks:
    - User assessment: Caller must be the record owner or an administrator.
    - Guest assessment: Caller must supply matching 'X-Claim-Token' header.
    """
    record = db.query(AssessmentRecord).filter(AssessmentRecord.id == assessment_id).first()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found.")

    if record.user_id is not None:
        if not optional_user or (optional_user.id != record.user_id and optional_user.role != "admin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You do not have permission to view this assessment."
            )
    else:
        # Guest assessment inspection requires X-Claim-Token header
        claim_header = request.headers.get("X-Claim-Token")
        if not claim_header or not record.claim_token_hash or not secure_compare(record.claim_token_hash, hash_token(claim_header)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: A valid claim token header is required to view guest assessment details."
            )

    return record


@router.post(
    "/solar/assessment/{assessment_id}/claim",
    dependencies=[Depends(verify_csrf)],
    summary="Claim Guest Assessment to Authenticated User Account"
)
def claim_assessment(
    assessment_id: int,
    req: ClaimAssessmentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Binds a previously unauthenticated guest assessment to the currently logged-in user.
    Requires submitting the unguessable raw claim token in the request body.
    Tokens are hashed and securely compared. Once claimed, the claim secret is cleared.
    """
    record = db.query(AssessmentRecord).filter(AssessmentRecord.id == assessment_id).first()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found.")

    if record.user_id is not None:
        if record.user_id == current_user.id:
            return {"message": "Assessment is already linked to your account.", "assessment_id": record.id}
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assessment has already been claimed by another user."
        )

    if not record.claim_token_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assessment is not claimable."
        )

    incoming_hash = hash_token(req.claim_token)
    if not secure_compare(record.claim_token_hash, incoming_hash):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid claim token. Claiming rejected."
        )

    # Transfer ownership to current user and erase one-time claim hash
    record.user_id = current_user.id
    record.claim_token_hash = None
    db.commit()

    return {
        "message": "Solar assessment successfully claimed and linked to your RoofwiseBD account.",
        "assessment_id": record.id
    }
