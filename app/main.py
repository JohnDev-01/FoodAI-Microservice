from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import routes_analytics, routes_predict_ai
from mangum import Mangum
from app.api.v1.routes_health import router as health_router
from app.api.v1.routes_email import router as email_router

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


app.include_router(health_router, prefix="/api/v1")
app.include_router(email_router, prefix="/api/v1")
app.include_router(routes_analytics.router, prefix="/api/v1")
app.include_router(routes_predict_ai.router, prefix="/api/v1")

# handler para Lambda
handler = Mangum(app)
