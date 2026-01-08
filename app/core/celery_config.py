from gevent import monkey
monkey.patch_all()

from celery import Celery


app = Celery("notifications-p")
app.conf.update(
    broker_url="redis://127.0.0.1:6379/0",
    result_backend="redis://127.0.0.1:6379/1",

    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",

    timezone="Europe/Moscow",
    enable_utc=True,  # recommendation

    task_track_started=True,  # отслеживаем начало выполнения
    task_soft_time_limit=25 * 60,  # мягкий лимит 25 мин - ловим SoftTimeLimitExceeded, но таска продолжает работать
    task_time_limit=30 * 60,  # Максимальное время выполнения (30 мин)

    task_acks_late=True,  # подтверждение задачи после выполнения
    task_reject_on_worker_lost=True,  # reconnect (on worker lost)
    broker_connection_retry_on_startup=True,  # reconnect (on startup)

    task_ignore_result=False,  # save results

    worker_prefetch_multiplier=1,  # берем только по одной задаче на гринлет
)


if __name__ == '__main__':
    app.start([
        "worker",
        "-P", "gevent",  # пул (механизм параллельного выполнения тасок)
        "--concurrency=3",  # кол-во гринлетов (супер легкий поток типо корутина на низком уровне) на 1 воркера
        # 3 так как это максимум тасок в минуту (лимитер настроен)
        "--loglevel=INFO",
        "-E",  # включаем события для мониторинга задач
        "--without-gossip",  # 1 воркер, не с кем общаться
        "--without-mingle",  # 1 воркер, не с кем общаться
    ])
