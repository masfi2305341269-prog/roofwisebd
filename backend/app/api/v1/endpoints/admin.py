from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database.database import get_db
from app.database.models import User, UserSession, AssessmentRecord
from app.schemas.auth import (
    AdminStatsResponse,
    AdminUserItem,
    AdminToggleUserStatusRequest
)
from app.api.deps import get_current_admin, verify_csrf

router = APIRouter(prefix="/admin", tags=["Administrator Management & System Analytics"])

@router.get("/stats", response_model=AdminStatsResponse, summary="Get Platform Analytics & KPIs")
def get_admin_stats(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Retrieves high-level system usage, user count, and solar sizing statistics."""
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    total_assessments = db.query(AssessmentRecord).count()
    guest_assessments = db.query(AssessmentRecord).filter(AssessmentRecord.user_id == None).count()
    user_assessments = db.query(AssessmentRecord).filter(AssessmentRecord.user_id != None).count()

    sums = db.query(
        func.coalesce(func.sum(AssessmentRecord.recommended_capacity_kwp), 0.0),
        func.coalesce(func.sum(AssessmentRecord.monthly_savings_bdt), 0.0)
    ).first()

    total_capacity_kwp = round(float(sums[0]), 2)
    total_monthly_savings_bdt = round(float(sums[1]), 2)

    return AdminStatsResponse(
        total_users=total_users,
        active_users=active_users,
        total_assessments=total_assessments,
        guest_assessments=guest_assessments,
        user_assessments=user_assessments,
        total_capacity_kwp=total_capacity_kwp,
        total_monthly_savings_bdt=total_monthly_savings_bdt
    )


@router.get("/users", response_model=List[AdminUserItem], summary="List All Registered Users")
def list_admin_users(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Returns list of registered platform users along with their role, status, and assessment counts."""
    users = db.query(User).order_by(User.id.desc()).all()
    results = []
    for u in users:
        assessment_cnt = db.query(AssessmentRecord).filter(AssessmentRecord.user_id == u.id).count()
        results.append(
            AdminUserItem(
                id=u.id,
                email=u.email,
                full_name=u.full_name,
                phone=u.phone,
                address=u.address,
                role=u.role,
                is_active=u.is_active,
                created_at=u.created_at,
                assessment_count=assessment_cnt
            )
        )
    return results


@router.put(
    "/users/{user_id}/status",
    dependencies=[Depends(verify_csrf)],
    summary="Toggle User Active Status"
)
def toggle_user_status(
    user_id: int,
    req: AdminToggleUserStatusRequest,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Activates or deactivates a user account.
    Prevents an admin from deactivating their own administrator account.
    Deactivating immediately revokes all active sessions for that user.
    """
    if admin.id == user_id and not req.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot deactivate your own administrator account."
        )

    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )

    target_user.is_active = req.is_active

    if not req.is_active:
        # Revoke all active sessions for this deactivated user
        db.query(UserSession).filter(
            UserSession.user_id == target_user.id,
            UserSession.revoked == False
        ).update({"revoked": True, "revoked_at": datetime.utcnow()})

    db.commit()
    status_label = "activated" if req.is_active else "deactivated"
    return {"message": f"User account {target_user.email} has been {status_label}."}


@router.get("/assessments", summary="List All Assessments (System-Wide)")
def list_all_assessments(
    limit: int = 50,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Allows administrators to inspect all solar assessments conducted across the platform."""
    records = db.query(AssessmentRecord).order_by(AssessmentRecord.id.desc()).limit(limit).all()
    results = []
    for r in records:
        user_info = None
        if r.user:
            user_info = {
                "id": r.user.id,
                "email": r.user.email,
                "full_name": r.user.full_name
            }
        results.append({
            "id": r.id,
            "created_at": r.created_at.isoformat(),
            "division": r.division,
            "district": r.district,
            "monthly_units_kwh": r.monthly_units_kwh,
            "recommended_capacity_kwp": r.recommended_capacity_kwp,
            "recommended_inverter_ac_kw": r.recommended_inverter_ac_kw,
            "panel_count": r.panel_count,
            "monthly_savings_bdt": r.monthly_savings_bdt,
            "sreda_compliant": r.sreda_compliant,
            "is_guest": r.user_id is None,
            "user": user_info
        })
    return results
