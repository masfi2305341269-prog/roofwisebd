from fastapi import APIRouter
from app.services.status_service import inspect_system_status
from app.schemas.status import SystemStatusResponse

router = APIRouter()

@router.get("/models/status", summary="Get ML Model Connection & Weights Status")
def get_models_status():
    status = inspect_system_status()
    return {
        "status": "success",
        "models": status.models
    }

@router.get("/datasets/status", summary="Get Raw Datasets Directory Status")
def get_datasets_status():
    status = inspect_system_status()
    return {
        "status": "success",
        "datasets": status.datasets
    }

@router.get("/system/status", response_model=SystemStatusResponse, summary="Get Full System Status")
def get_system_status():
    return inspect_system_status()
