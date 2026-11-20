from typing import Optional
from pydantic import BaseModel

class BillAnalysisResponse(BaseModel):
    filename: str
    file_type: str
    file_size_kb: float
    ocr_status: str  # "manual_review_needed", "ocr_service_pending", "extracted"
    extracted_units_kwh: Optional[float] = None
    extracted_bill_bdt: Optional[float] = None
    extracted_billing_period_days: Optional[int] = 30
    confidence_score: Optional[float] = None
    ocr_engine_message: str
    user_action_required: str
    is_demo_result: bool = True
