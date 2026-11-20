import shutil
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.core.config import settings
from app.schemas.rooftop import RooftopAnalysisRequest, RooftopAnalysisResponse
from app.services.rooftop_service import analyze_rooftop_potential

router = APIRouter()

@router.post("/rooftop/analyze", response_model=RooftopAnalysisResponse, summary="Analyze Rooftop Spatial Capacity")
def analyze_rooftop(req: RooftopAnalysisRequest):
    return analyze_rooftop_potential(req)

@router.post("/rooftop/upload-image", summary="Upload Rooftop Satellite or Site Photo")
async def upload_rooftop_image(file: UploadFile = File(...)):
    suffix = Path(file.filename or "temp.jpg").suffix.lower()
    if suffix not in {".jpg", ".jpeg", ".png", ".webp"}:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file extension {suffix}. Supported: JPG, JPEG, PNG, WEBP."
        )
    save_path = settings.UPLOAD_DIR / f"rooftop_{file.filename}"
    try:
        with open(save_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return {
            "filename": file.filename,
            "image_url": f"/uploads/rooftop_{file.filename}",
            "file_size_kb": round(save_path.stat().st_size / 1024, 1),
            "message": "Rooftop photo uploaded successfully for spatial and shading analysis."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rooftop photo upload error: {str(e)}")
