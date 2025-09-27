from fastapi import FastAPI
from app.api.v1.routes_health import router as health_router
from app.api.v1.routes_predict import router as predict_router

app = FastAPI(title="FoodAI Microservice")

app.include_router(health_router, prefix="/api/v1")
app.include_router(predict_router, prefix="/api/v1")
