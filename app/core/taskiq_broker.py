from aio_pika import ExchangeType, connect_robust
from asyncio import run

from taskiq_aio_pika import AioPikaBroker
from pydantic import BaseModel


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


def setup_broker() -> AioPikaBroker:
    config = RabbitConfig()

    async def declare_dl_structure(config: RabbitConfig) -> None:
        connection = await connect_robust(
            f"amqp://{config.username}:{config.password}@{config.host}:{config.port}"
        )

        async with connection:
            channel = await connection.channel()
            dlx = await channel.declare_exchange(config.dlx_exchange, ExchangeType.DIRECT, durable=True)
            dlq = await channel.declare_queue(
                config.dlx_queue, durable=True,
                arguments={"x-queue-mode": "lazy", "x-queue-type": "quorum", "x-message-ttl": 24*60*60*1000}
            )
            await dlq.bind(dlx, config.dlx_queue)

    try:
        run(declare_dl_structure(config=config))
    except Exception:
        # !!! no other exceptions !!!
        pass

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
            "x-queue-type": "quorum",  # распределенная, отказоустойчивая
            "x-max-priority": 3
        },

        max_connection_pool_size=3,  # макс 3 tcp соединений с рэббитом (что-то около золотой середины)
        prefetch_count=1,  # каждый потребитель берет макс 1 сообщение, чтобы не перегружался
        # (и чтобы лимиты бесплатного Google SMTP сервера не привысил)

        socket_timeout=30,  # 30с ждем ответа рэббита, после чего отваливаемся
        heartbeat=60,  # проверяем соединение каждые 60с
        blocked_connection_timeout=60,  # ждем 60с при перегрузки рэббита перед разрыванием соединения
    )

    return broker


# taskiq worker app.core.taskiq_broker:broker --fs-discover --tasks-pattern="app/google_mailing/send_email.py"
broker = setup_broker()
