from typing import List, Optional, Dict, Any
from pydantic import BaseModel

class SystemTier(BaseModel):
    tier_name: str # "Economical (60% Offset)", "Balanced (100% Target)", "Maximum Roof Potential"
    dc_capacity_kwp: float
    inverter_ac_kw: float
    panel_count: int
    panel_wattage_wp: int
    required_usable_area_sqft: float
    daily_generation_kwh: float
    monthly_generation_kwh: float
    annual_generation_kwh: float
    consumption_offset_pct: float
    est_turnkey_cost_bdt_min: float
    est_turnkey_cost_bdt_max: float
    est_monthly_savings_bdt: float
    est_annual_savings_bdt: float
    est_payback_years_min: float
    est_payback_years_max: float
    sreda_ac_compliant: bool
    sreda_note: str

class SredaComplianceStatus(BaseModel):
    is_compliant: bool
    sanctioned_load_kw: float
    recommended_inverter_ac_kw: float
    ac_to_sanctioned_ratio: float
    requires_three_phase: bool
    utility_approval_required: bool
    rule_summary: str
    advisory_text: str

class SolarRecommendationRequest(BaseModel):
    monthly_units_kwh: float
    total_roof_area_sqft: float
    sanctioned_load_kw: float = 2.0
    division: str = "Dhaka"
    roof_type: str = "concrete_flat"
    shading_condition: str = "low"
    usable_roof_area_sqft: Optional[float] = None
    custom_panel_wattage_wp: Optional[int] = 550

class SolarRecommendationResponse(BaseModel):
    recommended_system: SystemTier
    alternative_options: List[SystemTier]
    sreda_compliance: SredaComplianceStatus
    tariff_breakdown: Dict[str, Any]
    division: str
    monthly_psh_avg: float
    disclaimer: str
