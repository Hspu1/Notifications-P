from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, EmailStr

from app.google_mailing.dependencies import get_email_service
from app.google_mailing.send_email import EmailService

rout = APIRouter(prefix="/email", tags=["gmail"])


class SendEmailScheme(BaseModel):
    recipient: EmailStr
    subject: Annotated[str, Field(min_length=1, max_length=78)]
    body: Annotated[str, Field(min_length=1, max_length=100 * 1024)]


@rout.post("/send", status_code=202)
async def send_email(
        input_data: Annotated[SendEmailScheme, Depends()],
        email_service: EmailService = Depends(get_email_service)
):
    await email_service.send_email_async(
        recipient=input_data.recipient,
        subject=input_data.subject,
        body=input_data.body
    )
    return {"status": "accepted"}
