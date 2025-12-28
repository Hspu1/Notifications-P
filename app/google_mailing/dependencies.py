from fastapi import Depends, Request
from taskiq_aio_pika import AioPikaBroker

from app.google_mailing.send_email import EmailService


async def get_broker(request: Request) -> AioPikaBroker:
    return request.app.state.broker


def get_email_service(broker: AioPikaBroker = Depends(get_broker)) -> EmailService:
    return EmailService(broker)
