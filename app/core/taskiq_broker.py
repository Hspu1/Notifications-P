from contextlib import asynccontextmanager
from aio_pika import ExchangeType, connect_robust
from asyncio import run

from taskiq_aio_pika import AioPikaBroker
from pydantic_settings import BaseSettings


class RabbitConfig(BaseSettings):
    """model_config = SettingsConfigDict (+ .env)"""

    host: str = "localhost"
    port: int = 5672
    username: str = "guest"
    password: str = "guest"
    reconnect_on_fail: bool = True
    reconnect_interval: int = 5
    reconnect_max_attempts: int = 10

    main_exchange: str = "main_x"
    main_queue: str = "main_q"

    dlx_exchange: str = "dlx"
    dlx_queue: str = "dlq"
    dlx_routing_key: str = "dlq"

    declare_queues: bool = True
    declare_exchange: bool = True
    queue_durable: bool = True
    exchange_durable: bool = True

    max_connection_pool_size: int = 3  # макс 3 tcp соединений с рэббитом (что-то около золотой середины)
    prefetch_count: int = 1  # каждый потребитель берет макс 1 сообщение, чтобы не перегружался
    # (и чтобы лимиты бесплатного Google SMTP сервера не превысил)
    socket_timeout: int = 30  # 30с ждем ответа рэббита, после чего отваливаемся
    heartbeat: int = 60  # проверяем соединение каждые 60с
    blocked_connection_timeout: int = 60  # ждем 60с при перегрузки рэббита перед разрыванием соединения


@asynccontextmanager
async def get_connection(config: RabbitConfig):
    connection = await connect_robust(
        url=f"amqp://{config.username}:{config.password}@{config.host}:{config.port}",
        timeout=config.socket_timeout,
        heartbeat=config.heartbeat
    )
    try:
        yield connection
    finally:
        await connection.close()


async def declare_dlx(config: RabbitConfig):
    async with get_connection(config) as connection:
        async with connection.channel() as channel:
            dlx = await channel.declare_exchange(config.dlx_exchange, ExchangeType.DIRECT, durable=True)
            dlq = await channel.declare_queue(
                config.dlx_queue,
                durable=True,
                arguments={
                    "x-queue-type": "quorum",  # распределенная, отказоустойчивая
                    "x-message-ttl": 24 * 60 * 60 * 1000  # храним сообщения сутки в dlq
                }
            )
            await dlq.bind(dlx, config.dlx_routing_key)


async def setup_broker_async() -> AioPikaBroker:
    config = RabbitConfig()
    await declare_dlx(config)

    return AioPikaBroker(
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


def setup_broker() -> AioPikaBroker:
    return run(setup_broker_async())


# taskiq worker app.core.taskiq_broker:broker app.google_mailing.send_email
broker = setup_broker()
