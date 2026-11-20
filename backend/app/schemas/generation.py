from typing import List, Dict, Optional
from pydantic import BaseModel, Field

class GenerationPredictionRequest(BaseModel):
    system_capacity_kwp: float = Field(..., gt=0, example=3.5)
    division: str = Field("Dhaka", example="Dhaka")
    tilt_degrees: Optional[float] = Field(23.0, example=23.0)
    shading_factor: Optional[float] = Field(0.95, ge=0.5, le=1.0)
    month: Optional[int] = Field(None, ge=1, le=12, description="Specific month or full year")

class MonthlyGeneration(BaseModel):
    month_name: str
    month_index: int
    psh: float
    generation_kwh: float

class HourlyProfileItem(BaseModel):
    hour: int
    time_label: str
    generation_kw: float
    energy_kwh: float

class GenerationPredictionResponse(BaseModel):
    system_capacity_kwp: float
    division: str
    annual_generation_kwh: float
    average_daily_generation_kwh: float
    monthly_breakdown: List[MonthlyGeneration]
    hourly_sample_profile: List[HourlyProfileItem]
    model_status: str
    model_name: str
    is_demo: bool
    data_source: str
    prediction_explanation: str
    limitations_notice: str
