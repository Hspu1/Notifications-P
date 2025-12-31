from asyncio import run, get_event_loop, create_task

from taskiq_aio_pika import AioPikaBroker
from pydantic import BaseModel
from aio_pika import ExchangeType, connect_robust


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
        loop = get_event_loop()
        if loop.is_running():
            create_task(declare_dl_structure(config))
        else:
            run(declare_dl_structure(config))

    except RuntimeError:
        run(declare_dl_structure(config))
    #  !!! wb other exceptions !!!

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


        auto_delete=False,  # не удалять очередь автоматически при отключении потребителя
        exclusive=False,  # очередь доступна для нескольких потребителей


        persistent=True,  # сохранять сообщения на диске для устойчивости
        mandatory=True,  # гарантировать доставку сообщений
        max_connection_pool_size=10,  # макс 10 tcp соединений с рэббитом (что-то около золотой середины)
        prefetch_count=7,  # каждый потребитель берет макс 7 сообщений, чтобы не перегружался

        socket_timeout=10,  # 10с ждем ответа рэббита, после чего отваливаемся
        heartbeat=30,  # проверяем соединение каждые 30с
        blocked_connection_timeout=30,  # ждем 30с при перегрузки рэббита перед разрыванием соединения
        declare_queues_kwargs={
            "arguments": {
                "x-queue-type": "quorum",  # распределенная, отказоустойчивая
            }
        }
    )

    return broker


broker = setup_broker()
