from taskiq_aio_pika import AioPikaBroker
from pydantic import BaseModel
from aio_pika import ExchangeType, connect_robust
import asyncio


class RabbitConfig(BaseModel):
    host: str = "localhost"
    port: int = 5672
    username: str = "guest"
    password: str = "guest"

    main_exchange: str = "main_x"
    main_queue: str = "main_q"
    main_routing_key: str = main_queue

    dlx_exchange: str = "dlx"
    dlx_queue: str = "dlq"
    dlx_routing_key: str = dlx_queue


async def declare_dl_structure(config: RabbitConfig) -> None:
    connection = await connect_robust(
        f"amqp://{config.username}:{config.password}@{config.host}:{config.port}"
    )

    try:
        channel = await connection.channel()
        dlx_exchange = await channel.declare_exchange(
            config.dlx_exchange,
            type=ExchangeType.DIRECT,
            durable=True
        )
        dlq_queue = await channel.declare_queue(
            config.dlx_queue,
            durable=True,
            arguments={
                "x-queue-mode": "lazy"
            }
        )
        await dlq_queue.bind(dlx_exchange, config.dlx_routing_key)

    finally:
        await connection.close()


def setup_broker() -> AioPikaBroker:
    config = RabbitConfig()

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(declare_dl_structure(config))
        else:
            asyncio.run(declare_dl_structure(config))
    except RuntimeError:
        asyncio.run(declare_dl_structure(config))

    broker = AioPikaBroker(
        url=f"amqp://{config.username}:{config.password}@{config.host}:{config.port}",
        reconnect_on_fail=True,
        reconnect_interval=5,
        reconnect_max_attempts=10,

        queue_name=config.main_queue,
        exchange_name=config.main_exchange,
        routing_key=config.main_routing_key,
        declare_queues=True,
        declare_exchange=True,
        queue_durable=True,
        exchange_durable=True,
        queue_arguments={
            "x-dead-letter-exchange": config.dlx_exchange,
            "x-dead-letter-routing-key": config.dlx_routing_key,
        },

        auto_delete=False,
        exclusive=False,

        persistent=True,
        max_connection_pool_size=10,
        mandatory=True,
        prefetch_count=7,

        socket_timeout=10,
        heartbeat=30,
        blocked_connection_timeout=30,
    )

    return broker


broker = setup_broker()
