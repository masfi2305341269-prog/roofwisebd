import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_endpoint():
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["service"] == "RoofwiseBD"

def test_models_status_endpoint():
    res = client.get("/api/v1/models/status")
    assert res.status_code == 200
    data = res.json()
    assert "models" in data
    assert len(data["models"]) >= 2

def test_datasets_status_endpoint():
    res = client.get("/api/v1/datasets/status")
    assert res.status_code == 200
    data = res.json()
    assert "datasets" in data
    assert len(data["datasets"]) >= 4

def test_rooftop_analysis_endpoint():
    payload = {
        "total_area_sqft": 1500.0,
        "roof_type": "concrete_flat",
        "shading_condition": "low"
    }
    res = client.post("/api/v1/rooftop/analyze", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["usable_area_sqft"] == 1050.0  # 70%
    assert data["estimated_max_capacity_kwp"] > 0

def test_solar_recommendation_endpoint():
    payload = {
        "monthly_units_kwh": 320.0,
        "total_roof_area_sqft": 1200.0,
        "sanctioned_load_kw": 3.0,
        "division": "Dhaka"
    }
    res = client.post("/api/v1/solar/recommendation", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "recommended_system" in data
    assert "sreda_compliance" in data
    assert data["recommended_system"]["inverter_ac_kw"] <= 3.0

def test_battery_recommendation_endpoint():
    payload = {
        "appliances": [
            {"name": "Fan", "wattage": 75, "quantity": 2, "daily_usage_hours": 8, "is_critical": True},
            {"name": "Light", "wattage": 20, "quantity": 4, "daily_usage_hours": 6, "is_critical": True}
        ],
        "required_backup_hours": 4.0,
        "battery_chemistry": "lifepo4"
    }
    res = client.post("/api/v1/battery/recommendation", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["total_critical_load_watts"] == 230.0  # (75*2)+(20*4) = 150+80 = 230
    assert data["recommended_nominal_capacity_kwh"] > 0
