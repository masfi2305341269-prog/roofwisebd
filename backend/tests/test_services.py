import pytest
from app.core.tariffs import calculate_bangladesh_residential_bill, calculate_solar_bill_savings
from app.services.rooftop_service import analyze_rooftop_potential
from app.schemas.rooftop import RooftopAnalysisRequest
from app.services.solar_recommendation_service import generate_solar_recommendations
from app.schemas.recommendation import SolarRecommendationRequest
from app.services.battery_service import optimize_battery_storage
from app.schemas.battery import BatteryOptimizationRequest, ApplianceItem

def test_berc_2026_lifeline_tariff():
    # 40 units (lifeline <= 50)
    bill = calculate_bangladesh_residential_bill(units_kwh=40.0, sanctioned_load_kw=2.0)
    # Energy: 40 * 4.63 = 185.20 BDT
    assert bill["energy_charge_bdt"] == 185.20
    assert bill["demand_charge_bdt"] == 70.0  # 2 kW * 35
    assert bill["meter_rent_bdt"] == 40.0
    # Taxable: 185.20 + 70 = 255.20. VAT (5%): 12.76
    assert bill["vat_bdt"] == 12.76
    assert bill["total_bill_bdt"] == round(255.20 + 40.0 + 12.76, 2)

def test_berc_2026_multislab_tariff():
    # 350 units
    # Slabs:
    # 0-75: 75 * 5.26 = 394.50
    # 76-200 (125 units): 125 * 8.50 = 1062.50
    # 201-300 (100 units): 100 * 9.10 = 910.00
    # 301-400 (50 units): 50 * 9.62 = 481.00
    # Total energy: 394.50 + 1062.50 + 910.00 + 481.00 = 2848.00
    bill = calculate_bangladesh_residential_bill(units_kwh=350.0, sanctioned_load_kw=2.0)
    assert bill["energy_charge_bdt"] == 2848.00
    assert bill["demand_charge_bdt"] == 70.0
    # Taxable: 2918.00, VAT: 145.90, Meter: 40.0, Total: 3103.90
    assert bill["vat_bdt"] == 145.90
    assert bill["total_bill_bdt"] == 3103.90

def test_solar_savings_calculation():
    # 350 original units, 200 kWh solar offset
    savings = calculate_solar_bill_savings(
        original_units_kwh=350.0,
        solar_generated_kwh=200.0,
        sanctioned_load_kw=2.0
    )
    assert savings["original_bill_bdt"] == 3103.90
    assert savings["net_grid_units_kwh"] == 150.0
    assert savings["monthly_savings_bdt"] > 0
    assert savings["annual_savings_bdt"] == savings["monthly_savings_bdt"] * 12.0

def test_rooftop_analysis():
    req = RooftopAnalysisRequest(
        total_area_sqft=1000.0,
        roof_type="concrete_flat",
        shading_condition="low"
    )
    res = analyze_rooftop_potential(req)
    assert res.usable_area_sqft == 700.0  # 70% of 1000
    assert res.estimated_max_capacity_kwp > 0
    assert res.max_panel_count > 0
    assert "civil engineering" in res.structural_disclaimer.lower()

def test_sreda_2025_net_metering_compliance():
    # Case 1: Within sanctioned load (3 kW sanctioned load, 250 units consumption)
    req = SolarRecommendationRequest(
        monthly_units_kwh=250.0,
        total_roof_area_sqft=1200.0,
        sanctioned_load_kw=3.0,
        division="Dhaka"
    )
    rec = generate_solar_recommendations(req)
    balanced = rec.recommended_system
    # Inverter AC must be <= sanctioned load (3.0 kW)
    assert balanced.inverter_ac_kw <= 3.0
    assert rec.sreda_compliance.is_compliant is True

    # Case 2: Max roof capacity exceeding sanctioned load
    max_tier = next(t for t in rec.alternative_options if "Maximum" in t.tier_name)
    if max_tier.inverter_ac_kw > 3.0:
        assert max_tier.sreda_ac_compliant is False

def test_battery_storage_optimization():
    appliances = [
        ApplianceItem(name="LED Bulb", wattage=15.0, quantity=5, daily_usage_hours=6.0, is_critical=True),
        ApplianceItem(name="Ceiling Fan", wattage=75.0, quantity=3, daily_usage_hours=8.0, is_critical=True),
        ApplianceItem(name="WiFi Router", wattage=12.0, quantity=1, daily_usage_hours=24.0, is_critical=True),
    ]
    # Critical watts: (15*5) + (75*3) + (12*1) = 75 + 225 + 12 = 312 W
    req = BatteryOptimizationRequest(
        appliances=appliances,
        required_backup_hours=4.0,
        battery_chemistry="lifepo4",
        custom_dod=0.85,
        custom_inverter_eff=0.90,
        safety_margin=1.15
    )
    res = optimize_battery_storage(req)
    assert res.total_critical_load_watts == 312.0
    # Backup energy: 312 * 4 * 1.15 = 1435.2 Wh
    assert res.required_backup_energy_wh == 1435.2
    assert res.usable_capacity_required_kwh > 1.0
    assert res.recommended_nominal_capacity_kwh >= res.usable_capacity_required_kwh
    assert len(res.schedule_profile) == 24
