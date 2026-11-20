from typing import Optional, List
from pydantic import BaseModel, Field

class LocationInfo(BaseModel):
    division: str = Field(..., example="Dhaka")
    district: str = Field(..., example="Dhaka")
    area: Optional[str] = Field(None, example="Mirpur DOHS")
    latitude: Optional[float] = Field(None, example=23.8103)
    longitude: Optional[float] = Field(None, example=90.4125)

class ConsumptionInfo(BaseModel):
    monthly_units_kwh: float = Field(..., gt=0, example=350.0, description="Monthly electricity consumption in kWh")
    billing_period_days: int = Field(30, ge=1, le=365, example=30)
    bill_amount_bdt: Optional[float] = Field(None, ge=0, example=3200.0)
    sanctioned_load_kw: float = Field(2.0, gt=0, example=3.0, description="Customer utility sanctioned load in kW")
    consumer_category: str = Field("Residential", example="Residential")

class RooftopInfo(BaseModel):
    total_area_sqft: float = Field(..., gt=0, example=1200.0, description="Gross rooftop area in square feet")
    usable_area_sqft: Optional[float] = Field(None, description="Usable area excluding parapet, water tank, stairs")
    roof_type: str = Field("concrete_flat", example="concrete_flat") # concrete_flat, tin_shed, tiled
    shading_condition: str = Field("low", example="low") # none, low, medium, heavy
    orientation: Optional[str] = Field("South", example="South")
    tilt_degrees: Optional[float] = Field(23.0, example=23.0)
    roof_image_url: Optional[str] = None

class SolarAssessmentRequest(BaseModel):
    location: LocationInfo
    consumption: ConsumptionInfo
    rooftop: RooftopInfo
    bill_file_path: Optional[str] = None
    notes: Optional[str] = None

class SolarAssessmentResponse(BaseModel):
    id: Optional[int] = None
    created_at: str
    location: LocationInfo
    consumption: ConsumptionInfo
    rooftop: RooftopInfo
    recommended_capacity_kwp: float
    recommended_inverter_ac_kw: float
    panel_count: int
    daily_generation_kwh: float
    monthly_generation_kwh: float
    annual_generation_kwh: float
    monthly_savings_bdt: float
    estimated_payback_years: float
    sreda_compliant: bool
    sreda_advisory: str
    structural_disclaimer: str
    claim_token: Optional[str] = None
    is_guest: bool = False
