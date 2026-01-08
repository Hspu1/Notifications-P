from celery import Celery

# celery --app=app.core.celery_app worker --pool=solo --loglevel DEBUG
app = Celery(
    "notifications-p",
    broker="redis://127.0.0.1:6379/0",
    backend="redis://127.0.0.1:6379/1",
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Europe/Moscow',
)
