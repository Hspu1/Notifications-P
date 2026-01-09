from asyncio import run

from taskiq_aio_pika import AioPikaBroker
from taskiq_redis import RedisAsyncResultBackend

from app.core.configs.rabbit_conf import RabbitConfig, declare_dlx


async def setup_broker_async() -> AioPikaBroker:
    config = RabbitConfig()
    await declare_dlx(config)

    broker = AioPikaBroker(
        url=f"amqp://{config.username}:{config.password}@{config.host}:{config.port}",
        reconnect_on_fail=config.reconnect_on_fail,
        reconnect_interval=config.reconnect_interval,
        reconnect_max_attempts=config.reconnect_max_attempts,

        queue_name=config.main_queue,
        exchange_name=config.main_exchange,
        declare_queues=config.declare_queues,
        declare_exchange=config.declare_exchange,
        queue_durable=config.queue_durable,
        exchange_durable=config.exchange_durable,
        queue_arguments={
            "x-dead-letter-exchange": config.dlx_exchange,
            "x-dead-letter-routing-key": config.dlx_routing_key,
            "x-queue-type": "quorum",
            "x-max-priority": 3
        },

        max_connection_pool_size=config.max_connection_pool_size,
        prefetch_count=config.prefetch_count,
        socket_timeout=config.socket_timeout,
        heartbeat=config.heartbeat,
        blocked_connection_timeout=config.blocked_connection_timeout,
    )
    result_backend = RedisAsyncResultBackend(
        redis_url="redis://localhost:6379/2",
        result_ex_time=24 * 3600,  # 24 часа
        result_serializer="json",
    )

    return broker.with_result_backend(result_backend)


def setup_broker_sync() -> AioPikaBroker:
    return run(setup_broker_async())


# taskiq worker app.core.configs.taskiq_conf:broker app.google_mailing
broker = setup_broker_sync()
