from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # tu frontend local
        "https://foodai-online.web.app/", # dominio de producción
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api.v1.routes_health import router as health_router
from app.api.v1.routes_predict import router as predict_router
from app.api.v1.routes_email import router as email_router
app.include_router(health_router, prefix="/api/v1")
app.include_router(predict_router, prefix="/api/v1")
app.include_router(email_router, prefix="/api/v1")

# handler para Lambda
handler = Mangum(app)
