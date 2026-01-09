from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, EmailStr
from fastapi_limiter.depends import RateLimiter

from app.google_mailing.send_emails_async import create_task_async
from app.google_mailing.send_emails_sync import send_email

rout = APIRouter(prefix="/email", tags=["gmail"])


class SendEmailScheme(BaseModel):
    recipient: EmailStr
    subject: Annotated[str, Field(min_length=1, max_length=78)]
    body: Annotated[str, Field(min_length=1, max_length=100 * 1024)]


limiter = [
    Depends(RateLimiter(times=3, seconds=60)),  # minute
    Depends(RateLimiter(times=20, seconds=3600)),  # hourly
    Depends(RateLimiter(times=100, seconds=86400))  # daily
]


@rout.post("/send-using-taskiq", status_code=202, dependencies=limiter)
async def send_email_async(input_data: Annotated[SendEmailScheme, Depends()]):
    await create_task_async(recipient=input_data.recipient, subject=input_data.subject, body=input_data.body)
    return {"status": "accepted"}


@rout.post("/send-using-celery", status_code=202, dependencies=limiter)
def send_email_sync(input_data: Annotated[SendEmailScheme, Depends()]):
    result = send_email(recipient=input_data.recipient, subject=input_data.subject, body=input_data.body)
    return result
