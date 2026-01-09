from gevent import monkey
monkey.patch_all()

from app.core.configs.celery_conf import celery_app


if __name__ == '__main__':
    celery_app.start([
        "worker",
        "-P", "gevent",  # пул (механизм параллельного выполнения тасок)
        "--concurrency=3",
        # кол-во гринлетов (супер легкий поток типо корутина на низком уровне) на 1 воркера
        # 3 так как это максимум тасок в минуту (лимитер настроен)
        "--loglevel=INFO",
        "-E",  # включаем события для мониторинга задач
        "--without-gossip",  # 1 воркер, не с кем общаться
        "--without-mingle"  # 1 воркер, не с кем общаться
    ])
