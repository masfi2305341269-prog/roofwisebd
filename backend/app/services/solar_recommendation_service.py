"""
RoofwiseBD Solar Recommendation Engine
---------------------------------------
Determines optimal photovoltaic DC capacity (kWp), inverter AC capacity (kW),
panel layout, and financial returns under BERC 2026 tariffs and
SREDA Net Metering Guideline 2025 compliance rules.
"""

from typing import List, Dict, Any, Optional
import math
from app.core.config import settings
from app.core.tariffs import calculate_solar_bill_savings, calculate_bangladesh_residential_bill
from app.schemas.recommendation import (
    SolarRecommendationRequest,
    SolarRecommendationResponse,
    SystemTier,
    SredaComplianceStatus
)
from app.schemas.rooftop import RooftopAnalysisRequest
from app.services.rooftop_service import analyze_rooftop_potential

def build_tier(
    tier_name: str,
    target_dc_kwp: float,
    sanctioned_load_kw: float,
    monthly_units_kwh: float,
    avg_psh: float,
    max_roof_kwp: float,
    panel_wattage: int,
    panel_area_sqft: float
) -> SystemTier:
    # 1. Cap target capacity by physical rooftop availability
    dc_capacity = min(target_dc_kwp, max_roof_kwp)
    dc_capacity = max(0.5, round(dc_capacity, 2))
    
    # 2. Compute panel count
    panel_count = max(1, math.ceil((dc_capacity * 1000.0) / panel_wattage))
    actual_dc_kwp = round((panel_count * panel_wattage) / 1000.0, 2)
    
    # 3. Required usable roof space
    # ~27.2 sq ft per panel + spacing / tilt shadow buffer
    req_usable_sqft = round(panel_count * panel_area_sqft * 1.35, 1)

    # 4. Inverter AC capacity (DC / 1.20)
    inverter_ac_kw = round(actual_dc_kwp / settings.DEFAULT_INVERTER_DC_AC_RATIO, 2)
    
    # 5. SREDA Net Metering Guideline 2025 rule:
    # Renewable energy converter AC output must not exceed sanctioned load.
    sreda_ac_compliant = inverter_ac_kw <= sanctioned_load_kw
    
    if sreda_ac_compliant:
        sreda_note = f"Compliant: Inverter AC ({inverter_ac_kw} kW) is within sanctioned load ({sanctioned_load_kw} kW)."
    else:
        sreda_note = (
            f"Utility Sanction Required: Inverter AC ({inverter_ac_kw} kW) exceeds current sanctioned load "
            f"({sanctioned_load_kw} kW). Apply to electricity provider (DESCO/DPDC/BPDB/NESCO/BREB) for load enhancement."
        )

    # 6. Generation forecasting
    pr = settings.DEFAULT_SYSTEM_PR
    daily_gen_kwh = round(actual_dc_kwp * avg_psh * pr, 2)
    monthly_gen_kwh = round(daily_gen_kwh * 30.0, 1)
    annual_gen_kwh = round(daily_gen_kwh * 365.0, 1)
    
    offset_pct = min(100.0, round((monthly_gen_kwh / monthly_units_kwh) * 100, 1)) if monthly_units_kwh > 0 else 0.0

    # 7. Financial calculation using BERC 2026 tariff schedule
    savings = calculate_solar_bill_savings(
        original_units_kwh=monthly_units_kwh,
        solar_generated_kwh=monthly_gen_kwh,
        sanctioned_load_kw=sanctioned_load_kw
    )
    monthly_savings_bdt = savings["monthly_savings_bdt"]
    annual_savings_bdt = savings["annual_savings_bdt"]

    # Turnkey cost ranges in Bangladesh
    cost_min = round(actual_dc_kwp * settings.ESTIMATED_COST_PER_KWP_MIN_BDT, 0)
    cost_max = round(actual_dc_kwp * settings.ESTIMATED_COST_PER_KWP_MAX_BDT, 0)

    # Simple payback period
    payback_min = round(cost_min / annual_savings_bdt, 1) if annual_savings_bdt > 0 else 99.0
    payback_max = round(cost_max / annual_savings_bdt, 1) if annual_savings_bdt > 0 else 99.0

    return SystemTier(
        tier_name=tier_name,
        dc_capacity_kwp=actual_dc_kwp,
        inverter_ac_kw=inverter_ac_kw,
        panel_count=panel_count,
        panel_wattage_wp=panel_wattage,
        required_usable_area_sqft=req_usable_sqft,
        daily_generation_kwh=daily_gen_kwh,
        monthly_generation_kwh=monthly_gen_kwh,
        annual_generation_kwh=annual_gen_kwh,
        consumption_offset_pct=offset_pct,
        est_turnkey_cost_bdt_min=cost_min,
        est_turnkey_cost_bdt_max=cost_max,
        est_monthly_savings_bdt=monthly_savings_bdt,
        est_annual_savings_bdt=annual_savings_bdt,
        est_payback_years_min=payback_min,
        est_payback_years_max=payback_max,
        sreda_ac_compliant=sreda_ac_compliant,
        sreda_note=sreda_note
    )

def generate_solar_recommendations(req: SolarRecommendationRequest) -> SolarRecommendationResponse:
    division = req.division if req.division in settings.DIVISION_MONTHLY_PSH else "Dhaka"
    psh_list = settings.DIVISION_MONTHLY_PSH[division]
    avg_psh = sum(psh_list) / 12.0
    
    # 1. Analyze rooftop
    roof_analysis = analyze_rooftop_potential(RooftopAnalysisRequest(
        total_area_sqft=req.total_roof_area_sqft,
        roof_type=req.roof_type,
        shading_condition=req.shading_condition,
        manual_usable_area_sqft=req.usable_roof_area_sqft,
        panel_wattage_wp=req.custom_panel_wattage_wp or settings.DEFAULT_PANEL_WATTAGE_WP
    ))
    max_roof_dc_kwp = roof_analysis.estimated_max_capacity_kwp
    
    panel_wattage = req.custom_panel_wattage_wp or settings.DEFAULT_PANEL_WATTAGE_WP
    panel_area = settings.DEFAULT_PANEL_AREA_SQFT
    sanctioned_load = req.sanctioned_load_kw

    # 2. Target capacity for 100% monthly consumption offset
    # Monthly Generation = kWp * PSH * PR * 30 => kWp = Monthly Units / (PSH * PR * 30)
    pr = settings.DEFAULT_SYSTEM_PR * roof_analysis.shading_derate_factor
    kwp_for_100_pct = req.monthly_units_kwh / (avg_psh * pr * 30.0)

    # Respect SREDA 2025 rule for Balanced Tier:
    # Max inverter AC <= sanctioned load => Max DC = sanctioned_load * 1.20
    sreda_max_dc_kwp = sanctioned_load * settings.DEFAULT_INVERTER_DC_AC_RATIO
    balanced_target_dc = min(kwp_for_100_pct, sreda_max_dc_kwp, max_roof_dc_kwp)
    
    # Economical Tier: ~60% of balanced target
    economical_target_dc = balanced_target_dc * 0.60
    
    # Maximum Potential Tier: Full rooftop capacity
    max_target_dc = max_roof_dc_kwp

    # Build the 3 Tiers
    balanced_tier = build_tier(
        tier_name="Balanced (SREDA Compliant Target)",
        target_dc_kwp=balanced_target_dc,
        sanctioned_load_kw=sanctioned_load,
        monthly_units_kwh=req.monthly_units_kwh,
        avg_psh=avg_psh,
        max_roof_kwp=max_roof_dc_kwp,
        panel_wattage=panel_wattage,
        panel_area_sqft=panel_area
    )

    economical_tier = build_tier(
        tier_name="Economical (Quick Payback & Low Investment)",
        target_dc_kwp=economical_target_dc,
        sanctioned_load_kw=sanctioned_load,
        monthly_units_kwh=req.monthly_units_kwh,
        avg_psh=avg_psh,
        max_roof_kwp=max_roof_dc_kwp,
        panel_wattage=panel_wattage,
        panel_area_sqft=panel_area
    )

    max_tier = build_tier(
        tier_name="Maximum Roof Capacity",
        target_dc_kwp=max_target_dc,
        sanctioned_load_kw=sanctioned_load,
        monthly_units_kwh=req.monthly_units_kwh,
        avg_psh=avg_psh,
        max_roof_kwp=max_roof_dc_kwp,
        panel_wattage=panel_wattage,
        panel_area_sqft=panel_area
    )

    # SREDA Compliance Object for Recommended Tier
    ac_kw = balanced_tier.inverter_ac_kw
    is_compliant = balanced_tier.sreda_ac_compliant
    ratio = round(ac_kw / sanctioned_load, 2) if sanctioned_load > 0 else 1.0
    requires_three_phase = ac_kw > settings.THREE_PHASE_THRESHOLD_KW
    utility_approval = not is_compliant or requires_three_phase

    rule_summary = (
        f"Inverter AC: {ac_kw} kW vs Sanctioned Load: {sanctioned_load} kW (Ratio: {ratio}). "
        f"Grid Phase: {'Three-Phase Required (>10 kW)' if requires_three_phase else 'Standard Single/Three-Phase Compatible'}."
    )

    sreda_status = SredaComplianceStatus(
        is_compliant=is_compliant,
        sanctioned_load_kw=sanctioned_load,
        recommended_inverter_ac_kw=ac_kw,
        ac_to_sanctioned_ratio=ratio,
        requires_three_phase=requires_three_phase,
        utility_approval_required=utility_approval,
        rule_summary=rule_summary,
        advisory_text=settings.SREDA_ADVISORY
    )

    # Tariff breakdown for current consumption
    current_bill_calc = calculate_bangladesh_residential_bill(req.monthly_units_kwh, sanctioned_load)

    return SolarRecommendationResponse(
        recommended_system=balanced_tier,
        alternative_options=[economical_tier, max_tier],
        sreda_compliance=sreda_status,
        tariff_breakdown=current_bill_calc,
        division=division,
        monthly_psh_avg=round(avg_psh, 2),
        disclaimer=(
            "Advisory Notice: Turnkey prices, electricity tariffs, and payback periods are engineering planning estimates "
            "based on prevailing Bangladesh market averages. Official installation requires on-site civil structural and electrical survey."
        )
    )
