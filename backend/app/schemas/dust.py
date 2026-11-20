from typing import Optional
from pydantic import BaseModel

class DustPredictionResponse(BaseModel):
    filename: str
    image_width: int
    image_height: int
    classification: str  # "Clean", "Dusty", "Indeterminate"
    model_score: Optional[float] = None
    model_status: str  # "trained_model_active", "model_not_connected", "demo_mode"
    cleaning_recommendation: str
    maintenance_tip: str
    is_demo: bool
    explanation: str
