from typing import Optional
from pydantic import BaseModel, Field

class RooftopAnalysisRequest(BaseModel):
    total_area_sqft: float = Field(..., gt=0, example=1200.0)
    roof_type: str = Field("concrete_flat", example="concrete_flat") # concrete_flat, tin_shed, tiled
    shading_condition: str = Field("low", example="low") # none, low, medium, heavy
    manual_usable_area_sqft: Optional[float] = None
    panel_wattage_wp: Optional[int] = 550

class RooftopAnalysisResponse(BaseModel):
    total_area_sqft: float
    usable_area_sqft: float
    usable_ratio: float
    roof_type: str
    shading_condition: str
    shading_derate_factor: float
    estimated_max_capacity_kwp: float
    max_panel_count: int
    panel_specification: str
    structural_disclaimer: str
    recommendation_note: str
