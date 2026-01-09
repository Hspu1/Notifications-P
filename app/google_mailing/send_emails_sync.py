from email.message import EmailMessage
from os import getenv
from smtplib import SMTP_SSL, SMTPConnectError

from dotenv import load_dotenv

from app.core.configs.celery_conf import celery_app

load_dotenv()


@celery_app.task(
    name="send_email_sync",
    time_limit=40, max_retries=2, default_retry_delay=60, retry_backoff=True,
    retry_backoff_max=3600, retry_jitter=True, acks_late=True,
    autoretry_for=(SMTPConnectError, ConnectionError, TimeoutError)
)
def send_email(recipient: str, subject: str, body: str):
    sender_email, sender_psw = getenv("SENDER_EMAIL"), getenv("SENDER_PSW")

    msg = EmailMessage()
    msg["From"], msg["To"], msg["Subject"] = sender_email, recipient, subject
    msg.set_content(body)

    with SMTP_SSL("smtp.gmail.com", 465, timeout=30) as server:
        server.login(sender_email, sender_psw)
        server.send_message(msg)

    return {"status": "accepted"}
