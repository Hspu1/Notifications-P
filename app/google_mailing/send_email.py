from aiosmtplib import send
from pydantic import EmailStr
from email.message import EmailMessage
from os import getenv
from dotenv import load_dotenv
from taskiq_aio_pika import AioPikaBroker

load_dotenv()
# ! no limits on sending emails !


async def send_email(recipient: str, subject: str, body: str) -> None:
    sender_email, sender_psw = getenv("SENDER_EMAIL"), getenv("SENDER_PSW")

    msg = EmailMessage()
    msg["From"], msg["To"], msg["Subject"] = sender_email, recipient, subject
    msg.set_content(body)

    await send(
        msg, hostname="smtp.gmail.com", port=587,
        start_tls=True, username=sender_email,
        password=sender_psw, timeout=67
    )


class EmailService:
    def __init__(self, broker: AioPikaBroker):
        self.broker = broker
        self._email_task = self._register_task()

    def _register_task(self):
        @self.broker.task(task_name="save_email", timeout=70, priority=0, retry_count=3, retry_backoff=True, retry_backoff_delay=1, retry_jitter=True)
        async def send_email_interlayer(recipient: EmailStr, subject: str, body: str) -> None:
            await send_email(recipient=recipient, subject=subject, body=body)

        return send_email_interlayer

    async def send_email_async(self, recipient: EmailStr, subject: str, body: str):
        return await self._email_task.kiq(
            recipient=recipient,
            subject=subject,
            body=body
        )
