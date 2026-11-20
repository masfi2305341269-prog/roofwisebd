from fastapi import APIRouter
from app.schemas.generation import GenerationPredictionRequest, GenerationPredictionResponse
from app.services.generation_service import predict_solar_generation

router = APIRouter()

@router.post("/generation/predict", response_model=GenerationPredictionResponse, summary="Predict Solar Generation")
def predict_generation(req: GenerationPredictionRequest):
    return predict_solar_generation(req)
