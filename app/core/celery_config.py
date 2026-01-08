from gevent import monkey
monkey.patch_all()

from celery import Celery

app = Celery("notifications-p")

app.conf.update(
    broker_url="redis://127.0.0.1:6379/0",
    result_backend="redis://127.0.0.1:6379/1",

    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Europe/Moscow',
    worker_pool='gevent',
)


if __name__ == '__main__':
    app.start(['worker', '--loglevel=INFO'])
