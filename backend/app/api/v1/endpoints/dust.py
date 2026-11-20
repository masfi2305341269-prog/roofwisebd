import shutil
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.core.config import settings
from app.schemas.dust import DustPredictionResponse
from app.services.dust_service import analyze_panel_image

router = APIRouter()

ALLOWED_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}

@router.post("/dust/predict", response_model=DustPredictionResponse, summary="Predict Solar Panel Dust Accumulation")
async def predict_dust(file: UploadFile = File(...)):
    suffix = Path(file.filename or "temp.jpg").suffix.lower()
    if suffix not in ALLOWED_IMAGE_EXTS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file extension {suffix}. Supported: JPG, JPEG, PNG, WEBP."
        )

    # Save to uploads folder
    save_path = settings.UPLOAD_DIR / f"panel_{file.filename}"
    try:
        with open(save_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        result = analyze_panel_image(save_path)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image analysis error: {str(e)}")
