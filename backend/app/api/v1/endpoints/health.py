from fastapi import APIRouter
from app.core.config import settings

router = APIRouter()

@router.get("/health", summary="API Health Check")
def get_health():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION
    }
