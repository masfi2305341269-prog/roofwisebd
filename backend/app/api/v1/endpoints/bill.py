import shutil
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.core.config import settings
from app.schemas.bill import BillAnalysisResponse
from app.services.bill_service import process_bill_upload, ALLOWED_EXTENSIONS

router = APIRouter()

@router.post("/bill/analyze", response_model=BillAnalysisResponse, summary="Analyze Uploaded Electricity Bill")
async def analyze_bill(
    file: UploadFile = File(...),
    manual_units_kwh: Optional[float] = Form(None),
    manual_bill_bdt: Optional[float] = Form(None)
):
    suffix = Path(file.filename or "temp.pdf").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type {suffix}. Supported: PDF, JPG, JPEG, PNG."
        )

    save_path = settings.UPLOAD_DIR / f"bill_{file.filename}"
    try:
        with open(save_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        result = process_bill_upload(
            file_path=save_path,
            manual_units_kwh=manual_units_kwh,
            manual_bill_bdt=manual_bill_bdt
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bill processing error: {str(e)}")
