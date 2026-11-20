from fastapi import APIRouter
from app.schemas.battery import BatteryOptimizationRequest, BatteryOptimizationResponse
from app.services.battery_service import optimize_battery_storage

router = APIRouter()

@router.post("/battery/recommendation", response_model=BatteryOptimizationResponse, summary="Optimize Battery Backup Storage")
def get_battery_recommendation(req: BatteryOptimizationRequest):
    return optimize_battery_storage(req)
