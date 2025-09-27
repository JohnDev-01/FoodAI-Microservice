from fastapi import APIRouter
from app.models.predict import PredictIn, PredictOut
from app.services.predictor import predict_demand

router = APIRouter()

@router.post("/predict", response_model=PredictOut, tags=["ml"])
def predict(payload: PredictIn):
    yhat = predict_demand(payload.day_of_week, payload.is_holiday, payload.temperature_c)
    return PredictOut(demand=yhat)
