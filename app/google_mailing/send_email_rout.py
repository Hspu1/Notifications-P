from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, EmailStr

from app.google_mailing.send_email import send_email_interlayer

rout = APIRouter(prefix="/email", tags=["gmail"])


class SendEmailScheme(BaseModel):
    recipient: EmailStr
    subject: Annotated[str, Field(min_length=1, max_length=78)]
    body: Annotated[str, Field(min_length=1, max_length=100 * 1024)]


@rout.post("/send", status_code=202)
async def send(input_data: Annotated[SendEmailScheme, Depends()]) -> dict[str, str]:
    await send_email_interlayer.kiq(
        recipient=input_data.recipient,
        subject=input_data.subject, body=input_data.body
    )

    return {"status": "success"}
