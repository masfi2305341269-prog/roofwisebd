from fastapi import APIRouter
from app.api.v1.endpoints import (
    health,
    solar,
    bill,
    generation,
    dust,
    rooftop,
    battery,
    status,
    auth,
    admin
)

api_router = APIRouter()

# Mount all endpoint routers
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(auth.router)
api_router.include_router(admin.router)
api_router.include_router(solar.router, tags=["Solar Assessment & Recommendations"])
api_router.include_router(bill.router, tags=["Electricity Bill Analysis"])
api_router.include_router(generation.router, tags=["Generation Prediction (ML 1)"])
api_router.include_router(dust.router, tags=["Dust Detection (ML 2)"])
api_router.include_router(rooftop.router, tags=["Rooftop Spatial Analysis"])
api_router.include_router(battery.router, tags=["Battery Backup Optimization"])
api_router.include_router(status.router, tags=["System, Models & Datasets Registry"])

