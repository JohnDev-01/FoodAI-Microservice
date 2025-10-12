from pydantic import BaseModel, EmailStr


class EmailRequest(BaseModel):
    to: EmailStr
    subject: str
    html: str
