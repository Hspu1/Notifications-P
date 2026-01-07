from email.message import EmailMessage
from os import getenv
from dotenv import load_dotenv

from aiosmtplib import send
from pydantic import EmailStr

from app.core.taskiq_broker import broker

load_dotenv()


async def send_email(recipient: str, subject: str, body: str) -> None:
    sender_email, sender_psw = getenv("SENDER_EMAIL"), getenv("SENDER_PSW")

    msg = EmailMessage()
    msg["From"], msg["To"], msg["Subject"] = sender_email, recipient, subject
    msg.set_content(body)

    await send(
        msg, hostname="smtp.gmail.com", port=587,
        start_tls=True, username=sender_email,
        password=sender_psw, timeout=30
    )


@broker.task(task_name="save_email", timeout=40, priority=0, retry_count=2, retry_backoff=True, retry_backoff_delay=60, retry_jitter=True)
async def send_email_async(recipient: EmailStr, subject: str, body: str):
    # raise Exception("Test DLQ")
    await send_email(recipient=recipient, subject=subject, body=body)


async def create_task_async(recipient: EmailStr, subject: str, body: str):
    return await send_email_async.kiq(recipient=recipient, subject=subject, body=body)
