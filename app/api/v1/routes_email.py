from fastapi import APIRouter, HTTPException, status

from app.models.email import EmailRequest
from app.services.email_sender import EmailServiceError, send_email_via_api

router = APIRouter()


@router.post("/email/send", tags=["email"])
async def send_email(payload: EmailRequest):
    try:
        return await send_email_via_api(payload)
    except EmailServiceError as exc:
        http_status = exc.status_code or status.HTTP_502_BAD_GATEWAY
        raise HTTPException(status_code=http_status, detail=str(exc)) from exc
