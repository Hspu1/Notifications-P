from taskiq_aio_pika import AioPikaBroker
from pydantic import BaseModel
from aio_pika import ExchangeType, connect_robust

from asyncio import run


class RabbitConfig(BaseModel):
    host: str = "localhost"
    port: int = 5672
    username: str = "guest"
    password: str = "guest"

    main_exchange: str = "taskiq_exchange"
    dlx_exchange: str = "dlx_taskiq_exchange"

    main_queue: str = "taskiq_queue"
    dlq_queue: str = "dlq_taskiq_queue"

    main_routing_key: str = main_queue
    dlq_routing_key: str = dlq_queue


class RabbitMQSetup:
    def __init__(self, config: RabbitConfig):
        (
            self.config, self.connection, self.channel,
            self.main_exchange, self.dlx_exchange,
            self.main_queue, self.dlq_queue
        ) = (config, None, None, None, None, None, None)

    async def connect(self) -> None:
        connection_string = (
            f"amqp://{self.config.username}:{self.config.password}"
            f"@{self.config.host}:{self.config.port}/"
        )
        self.connection = await connect_robust(connection_string)
        self.channel = await self.connection.channel()

    async def close(self) -> None:
        if self.connection:
            await self.connection.close()

    async def declare_exchanges(self) -> None:
        self.main_exchange = await self.channel.declare_exchange(
            name=self.config.main_exchange,
            durable=True,
            type=ExchangeType.TOPIC
        )
        self.dlx_exchange = await self.channel.declare_exchange(
            name=self.config.dlx_exchange,
            durable=True,
            type=ExchangeType.TOPIC
        )

    async def declare_queues(self) -> None:
        self.main_queue = await self.channel.declare_queue(
            name=self.config.main_queue,
            durable=True,
            arguments={
                "x-dead-letter-exchange": self.config.dlx_exchange,
                "x-dead-letter-routing-key": self.config.dlq_routing_key,
            }
        )
        self.dlq_queue = await self.channel.declare_queue(
            name=self.config.dlq_queue,
            durable=True,
        )

    async def bind_queues(self) -> None:
        await self.main_queue.bind(
            exchange=self.main_exchange,
            routing_key=self.config.main_routing_key
        )
        await self.dlq_queue.bind(
            exchange=self.dlx_exchange,
            routing_key=self.config.dlq_routing_key
        )

    async def setup_all(self) -> None:
        try:
            await self.connect()
            await self.declare_exchanges()
            await self.declare_queues()
            await self.bind_queues()

        except (ConnectionError, TimeoutError, ValueError):
            await self.close()
            raise

        except Exception:
            await self.close()
            raise


async def preconfigure_rabbitmq():
    config = RabbitConfig()
    rabbit_setup = RabbitMQSetup(config)
    await rabbit_setup.setup_all()


async def setup_broker() -> AioPikaBroker:
    await preconfigure_rabbitmq()
    config = RabbitConfig()

    broker = AioPikaBroker(
        url=f"amqp://{config.username}:{config.password}@{config.host}:{config.port}",

        queue_name=config.main_queue,
        exchange_name=config.main_exchange,
        dead_letter_queue_name=config.dlq_queue,
        dead_letter_exchange_name=config.dlx_exchange,

        queue_arguments={
            "x-dead-letter-exchange": config.dlx_exchange,
            "x-dead-letter-routing-key": config.dlq_routing_key,
        },

        persistent=True,
        queue_durable=True,
        exchange_durable=True,
        reconnect_on_fail=True,
        prefetch_count=20
    )
    return broker


async def create_worker_broker():
    return await setup_broker()

# taskiq worker app.core.taskiq_broker:broker --fs-discover --tasks-pattern="app/google_mailing/send_email.py"
broker = run(create_worker_broker())
