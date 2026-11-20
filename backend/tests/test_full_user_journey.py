"""
RoofwiseBD - End-to-End User Journey & Comprehensive Feature Test Suite
Covers all core modules:
- Supabase Auth Registration, Provisioning & Profile Update
- Rooftop Spatial Sizing & Photo Upload
- Electricity Bill Upload & OCR Analysis
- BERC 2026 Tariff Calculation & SREDA 2025 Net Metering Compliance
- Solar Assessment Submission & Portfolio History Isolation
- Guest Assessment Creation & Authenticated Claiming
- Machine Learning 1: Generation Prediction (XGBoost / NASA POWER)
- Machine Learning 2: Solar Panel Dust Detection (MobileNetV2 / SolNet)
- Battery Capacity Optimization & 24-Hour SOC Simulation
- Admin Analytics, User Management & RBAC Privilege Enforcement
"""

import io
import time
import uuid
from typing import Dict, Any
import jwt
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from main import app
from app.core.config import settings
from app.database.database import SessionLocal
from app.database.models import User, AssessmentRecord

FAKE_SUPABASE_JWT_SECRET = "test_supabase_jwt_secret_32_bytes_long!!"

def make_supabase_jwt(
    auth_uid: str,
    email: str = "test@roofwisebd.com",
    role: str = "authenticated",
    app_metadata: dict = None,
    user_metadata: dict = None,
    secret: str = FAKE_SUPABASE_JWT_SECRET,
    algorithm: str = "HS256"
) -> str:
    now = int(time.time())
    payload = {
        "sub": auth_uid,
        "email": email,
        "role": role,
        "aud": "authenticated",
        "app_metadata": app_metadata or {"provider": "email", "providers": ["email"]},
        "user_metadata": user_metadata or {"full_name": "Test User", "email_verified": True},
        "email_confirmed_at": "2026-01-01T00:00:00Z",
        "email_verified": True,
        "iat": now,
        "exp": now + 3600
    }
    return jwt.encode(payload, secret, algorithm=algorithm)


class TestFullUserJourney:
    @pytest.fixture(autouse=True)
    def setup_supabase_env(self, monkeypatch):
        monkeypatch.setattr(settings, "AUTH_MODE", "supabase")
        monkeypatch.setattr(settings, "SUPABASE_JWT_SECRET", FAKE_SUPABASE_JWT_SECRET)
        monkeypatch.setattr(settings, "SUPABASE_URL", "https://test-project.supabase.co")

    def test_01_platform_health_and_status(self):
        client = TestClient(app)
        res_health = client.get("/api/v1/health")
        assert res_health.status_code == 200
        assert res_health.json()["status"] == "healthy"

        res_status = client.get("/api/v1/system/status")
        assert res_status.status_code == 200
        data = res_status.json()
        assert "berc_tariff_schedule" in data
        assert "sreda_guideline_active" in data
        assert len(data["models"]) >= 2

    def test_02_registration_provisioning_and_profile_update(self):
        client = TestClient(app)
        user_uid = str(uuid.uuid4())
        user_email = f"user_{int(time.time())}@roofwisebd.com"
        user_token = make_supabase_jwt(auth_uid=user_uid, email=user_email)

        # 1. Provision profile
        res_prov = client.post(
            "/api/v1/auth/provision-profile",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert res_prov.status_code in [200, 201]
        assert res_prov.json()["email"] == user_email
        assert res_prov.json()["role"] == "user"

        # 2. Get profile (/auth/me)
        res_me = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert res_me.status_code == 200
        assert res_me.json()["email"] == user_email

        # 3. Update profile (PUT /auth/me)
        res_update = client.put(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {user_token}"},
            json={
                "full_name": "Engr. Tanvir Ahmed",
                "phone": "+8801711998877",
                "address": "Sector 4, Uttara, Dhaka"
            }
        )
        assert res_update.status_code == 200
        updated = res_update.json()
        assert updated["full_name"] == "Engr. Tanvir Ahmed"
        assert updated["phone"] == "+8801711998877"

    def test_03_rooftop_spatial_analysis_and_photo_upload(self):
        client = TestClient(app)

        # 1. Upload rooftop site photo
        img = Image.new("RGB", (320, 240), color=(120, 150, 90))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        buf.seek(0)

        res_upload = client.post(
            "/api/v1/rooftop/upload-image",
            files={"file": ("rooftop_survey.jpg", buf, "image/jpeg")}
        )
        assert res_upload.status_code == 200
        assert "image_url" in res_upload.json()
        assert "rooftop_survey.jpg" in res_upload.json()["filename"]

        # 2. Analyze spatial potential
        res_analysis = client.post(
            "/api/v1/rooftop/analyze",
            json={
                "total_area_sqft": 1500.0,
                "roof_type": "concrete_flat",
                "shading_condition": "low"
            }
        )
        assert res_analysis.status_code == 200
        data = res_analysis.json()
        assert data["usable_area_sqft"] == 1050.0  # 70% of 1500
        assert data["estimated_max_capacity_kwp"] > 0
        assert data["max_panel_count"] > 0

    def test_04_bill_upload_and_analysis(self):
        client = TestClient(app)
        pdf_bytes = b"%PDF-1.4 official desco utility bill 420 kWh"
        buf = io.BytesIO(pdf_bytes)

        res = client.post(
            "/api/v1/bill/analyze",
            files={"file": ("desco_bill.pdf", buf, "application/pdf")},
            data={"manual_units_kwh": "420.0"}
        )
        assert res.status_code == 200
        data = res.json()
        assert data["extracted_units_kwh"] == 420.0
        assert data["ocr_status"] == "manual_confirmed"

    def test_05_solar_recommendation_and_berc_sreda_engine(self):
        client = TestClient(app)

        # Case A: System within sanctioned load (SREDA Compliant)
        res_rec = client.post(
            "/api/v1/solar/recommendation",
            json={
                "monthly_units_kwh": 350.0,
                "total_roof_area_sqft": 1200.0,
                "sanctioned_load_kw": 5.0,
                "division": "Dhaka",
                "roof_type": "concrete_flat",
                "shading_condition": "low"
            }
        )
        assert res_rec.status_code == 200
        data = res_rec.json()
        assert data["sreda_compliance"]["is_compliant"] is True
        assert data["sreda_compliance"]["sanctioned_load_kw"] == 5.0
        assert data["tariff_breakdown"]["total_bill_bdt"] > 0
        assert len(data["tariff_breakdown"]["slab_breakdown"]) > 0

        # Case B: System exceeding sanctioned load (SREDA Flags Utility Sanction Required)
        res_exceed = client.post(
            "/api/v1/solar/recommendation",
            json={
                "monthly_units_kwh": 650.0,
                "total_roof_area_sqft": 2000.0,
                "sanctioned_load_kw": 2.0,
                "division": "Dhaka"
            }
        )
        assert res_exceed.status_code == 200
        assert res_exceed.json()["sreda_compliance"]["is_compliant"] is False

    def test_06_solar_assessment_submission_and_user_history(self):
        client = TestClient(app)
        user_uid = str(uuid.uuid4())
        user_token = make_supabase_jwt(auth_uid=user_uid, email="portfolio_user@roofwisebd.com")

        # Provision user
        client.post("/api/v1/auth/provision-profile", headers={"Authorization": f"Bearer {user_token}"})

        # Submit assessment
        assessment_payload = {
            "location": {"division": "Chattogram", "district": "Chattogram", "area": "Agrabad"},
            "consumption": {"monthly_units_kwh": 400.0, "billing_period_days": 30, "sanctioned_load_kw": 5.0, "consumer_category": "Residential"},
            "rooftop": {"total_area_sqft": 1400.0, "roof_type": "concrete_flat", "shading_condition": "low", "roof_image_url": "/uploads/roof.jpg"}
        }
        res_sub = client.post(
            "/api/v1/solar/assessment",
            headers={"Authorization": f"Bearer {user_token}"},
            json=assessment_payload
        )
        assert res_sub.status_code == 200
        assessment_id = res_sub.json()["id"]
        assert res_sub.json()["is_guest"] is False

        # Verify appears in user's saved assessments history
        res_history = client.get(
            "/api/v1/solar/user/assessments",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert res_history.status_code == 200
        history_items = res_history.json()
        assert len(history_items) >= 1
        assert any(item["id"] == assessment_id for item in history_items)

    def test_07_guest_assessment_and_authenticated_claiming(self):
        client = TestClient(app)
        guest_payload = {
            "location": {"division": "Rajshahi", "district": "Rajshahi"},
            "consumption": {"monthly_units_kwh": 300.0, "sanctioned_load_kw": 3.0},
            "rooftop": {"total_area_sqft": 900.0, "roof_type": "tin_shed", "shading_condition": "none"}
        }
        res_guest = client.post("/api/v1/solar/assessment", json=guest_payload)
        assert res_guest.status_code == 200
        guest_data = res_guest.json()
        assert guest_data["is_guest"] is True
        claim_token = guest_data["claim_token"]
        assessment_id = guest_data["id"]

        # Authenticated user claims it
        user_uid = str(uuid.uuid4())
        user_token = make_supabase_jwt(auth_uid=user_uid, email="claimant@roofwisebd.com")
        client.post("/api/v1/auth/provision-profile", headers={"Authorization": f"Bearer {user_token}"})

        res_claim = client.post(
            f"/api/v1/solar/assessment/{assessment_id}/claim",
            headers={"Authorization": f"Bearer {user_token}"},
            json={"claim_token": claim_token}
        )
        assert res_claim.status_code == 200
        assert "claimed" in res_claim.json()["message"].lower()

    def test_08_machine_learning_generation_prediction(self):
        client = TestClient(app)
        res_pred = client.post(
            "/api/v1/generation/predict",
            json={
                "system_capacity_kwp": 4.5,
                "division": "Dhaka",
                "tilt_degrees": 23.0,
                "shading_factor": 0.95
            }
        )
        assert res_pred.status_code == 200
        data = res_pred.json()
        assert data["annual_generation_kwh"] > 0
        assert data["average_daily_generation_kwh"] > 0
        assert len(data["monthly_breakdown"]) == 12
        assert len(data["hourly_sample_profile"]) == 24

    def test_09_machine_learning_dust_detection(self):
        client = TestClient(app)
        img = Image.new("RGB", (224, 224), color=(60, 60, 60))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        buf.seek(0)

        res_dust = client.post(
            "/api/v1/dust/predict",
            files={"file": ("panel_field.jpg", buf, "image/jpeg")}
        )
        assert res_dust.status_code == 200
        data = res_dust.json()
        assert data["classification"] in ["Clean", "Dusty"]
        assert len(data["cleaning_recommendation"]) > 10

    def test_10_battery_optimizer_appliance_inventory(self):
        client = TestClient(app)
        res_bat = client.post(
            "/api/v1/battery/recommendation",
            json={
                "appliances": [
                    {"name": "Fan", "wattage": 75, "quantity": 3, "daily_usage_hours": 8, "is_critical": True},
                    {"name": "Light", "wattage": 15, "quantity": 4, "daily_usage_hours": 6, "is_critical": True},
                    {"name": "Router", "wattage": 12, "quantity": 1, "daily_usage_hours": 24, "is_critical": True}
                ],
                "required_backup_hours": 4.0,
                "battery_chemistry": "lifepo4",
                "custom_dod": 0.85,
                "custom_inverter_eff": 0.90
            }
        )
        assert res_bat.status_code == 200
        data = res_bat.json()
        assert data["recommended_nominal_capacity_kwh"] > 0
        assert data["usable_capacity_required_kwh"] > 0
        assert len(data["schedule_profile"]) == 24

    def test_11_admin_portal_analytics_and_governance(self):
        client = TestClient(app)
        admin_uid = str(uuid.uuid4())
        admin_email = f"admin_{int(time.time())}@roofwisebd.com"
        admin_token = make_supabase_jwt(auth_uid=admin_uid, email=admin_email)

        # Insert admin user record in test DB
        db = SessionLocal()
        admin = User(
            email=admin_email,
            full_name="Platform Administrator",
            role="admin",
            is_active=True,
            auth_user_id=admin_uid
        )
        # Also create a regular user to test status toggling
        target_uid = str(uuid.uuid4())
        target_user = User(
            email=f"target_{int(time.time())}@roofwisebd.com",
            full_name="Target User",
            role="user",
            is_active=True,
            auth_user_id=target_uid
        )
        db.add(admin)
        db.add(target_user)
        db.commit()
        db.refresh(target_user)
        target_id = target_user.id
        db.close()

        # 1. Admin Stats
        res_stats = client.get("/api/v1/admin/stats", headers={"Authorization": f"Bearer {admin_token}"})
        assert res_stats.status_code == 200
        assert res_stats.json()["total_users"] >= 2

        # 2. Admin Users
        res_users = client.get("/api/v1/admin/users", headers={"Authorization": f"Bearer {admin_token}"})
        assert res_users.status_code == 200
        assert len(res_users.json()) >= 2

        # 3. Admin Assessments
        res_assessments = client.get("/api/v1/admin/assessments", headers={"Authorization": f"Bearer {admin_token}"})
        assert res_assessments.status_code == 200

        # 4. Non-admin forbidden
        user_uid = str(uuid.uuid4())
        user_token = make_supabase_jwt(auth_uid=user_uid, email="standard_user@roofwisebd.com")
        client.post("/api/v1/auth/provision-profile", headers={"Authorization": f"Bearer {user_token}"})
        res_denied = client.get("/api/v1/admin/stats", headers={"Authorization": f"Bearer {user_token}"})
        assert res_denied.status_code == 403

        # 5. Toggle target user status (Deactivate)
        res_deact = client.put(
            f"/api/v1/admin/users/{target_id}/status",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"is_active": False}
        )
        assert res_deact.status_code == 200
        assert "deactivated" in res_deact.json()["message"]

        # 6. Toggle target user status (Reactivate)
        res_act = client.put(
            f"/api/v1/admin/users/{target_id}/status",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"is_active": True}
        )
        assert res_act.status_code == 200
        assert "activated" in res_act.json()["message"]
