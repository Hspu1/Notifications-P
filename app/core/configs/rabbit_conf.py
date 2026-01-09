from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from aio_pika import ExchangeType, connect_robust, RobustConnection

from pydantic import BaseModel


class RabbitConfig(BaseModel):
    """BaseSettings model_config = SettingsConfigDict (+ .env)"""

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
async def get_connection(config: RabbitConfig) -> AsyncIterator[RobustConnection]:
    connection = await connect_robust(
        url=f"amqp://{config.username}:{config.password}@{config.host}:{config.port}",
        timeout=config.socket_timeout,
        heartbeat=config.heartbeat
    )
    try:
        yield connection
    finally:
        await connection.close()


async def declare_dlx(config: RabbitConfig) -> None:
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
