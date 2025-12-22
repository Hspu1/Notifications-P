from aiosmtplib import send
from pydantic import EmailStr

from app.core.taskiq_broker import broker

from email.message import EmailMessage
from os import getenv
from dotenv import load_dotenv

load_dotenv()
# ! no limits on sending emails !


async def send_email(recipient: str, subject: str, body: str) -> None:
    sender_email, sender_psw = getenv("SENDER_EMAIL"), getenv("SENDER_PSW")

    msg = EmailMessage()
    msg["From"], msg["To"], msg["Subject"] = sender_email, recipient, subject
    msg.set_content(body)

    await send(
        msg, hostname="smtp.gmail.com", port=587, start_tls=True,
        username=sender_email, password=sender_psw, timeout=67
    )


@broker.task(
    task_name="save_email", timeout=70, priority=0, retry_count=3,
    retry_backoff=True,  # Включен экспоненциальный бэкоф
    retry_backoff_delay=1,  # Базовая задержка: 1 секунда
    retry_jitter=True,  # Включена случайная вариация ±30%
    # Бэкоф с jitter:
    # 1) 0.7 - 1.3 секунды   (1 сек ±30%)
    # 2) 1.4 - 2.6 секунды   (2 сек ±30%)
    # 3) 2.8 - 5.2 секунды   (4 сек ±30%)
)
async def send_email_interlayer(recipient: EmailStr, subject: str, body: str) -> None:
    await send_email(recipient=recipient, subject=subject, body=body)
