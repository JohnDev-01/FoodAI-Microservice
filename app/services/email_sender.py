from typing import Any, Dict

import httpx

from app.models.email import EmailRequest

EMAIL_API_URL = "https://mnnd3b5qhrn3bwcalbtddbg7p40lbsgr.lambda-url.us-east-2.on.aws/"


class EmailServiceError(RuntimeError):
    """Raised when the external email API call fails."""

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


async def send_email_via_api(payload: EmailRequest) -> Dict[str, Any]:
    """Forward the email payload to the external provider and return its JSON response."""
    async with httpx.AsyncClient(timeout=httpx.Timeout(10.0, connect=5.0)) as client:
        try:
            response = await client.post(EMAIL_API_URL, json=payload.model_dump())
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            # Propagate status errors with context for upstream handling.
            raise EmailServiceError(
                f"Email API responded with status {exc.response.status_code}",
                status_code=exc.response.status_code,
            ) from exc
        except httpx.HTTPError as exc:
            # Catch network, timeout and protocol issues.
            raise EmailServiceError("Error while calling the email API") from exc

    if response.headers.get("content-type", "").startswith("application/json"):
        return response.json()

    # Fallback to raw text if no JSON is returned.
    return {"message": response.text}
