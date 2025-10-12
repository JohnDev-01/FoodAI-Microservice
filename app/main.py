from fastapi import FastAPI
from mangum import Mangum

app = FastAPI()


from app.api.v1.routes_health import router as health_router
from app.api.v1.routes_predict import router as predict_router
from app.api.v1.routes_email import router as email_router
app.include_router(health_router, prefix="/api/v1")
app.include_router(predict_router, prefix="/api/v1")
app.include_router(email_router, prefix="/api/v1")

# handler para Lambda
handler = Mangum(app)
