from fastapi import APIRouter

router = APIRouter()

@router.get("/health", tags=["health"])
def health():
    return {"status": "ok", "message": "Service esta corriendo correctamente..."}

@router.get("/ok", tags=["ok"])
def ok():
    return {"message": "Api en funcionamiento..."}