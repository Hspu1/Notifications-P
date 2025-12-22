from taskiq_aio_pika import AioPikaBroker

# taskiq worker app.core.taskiq_broker:broker --fs-discover --tasks-pattern="app/google_mailing/send_email.py"
broker = AioPikaBroker(
    url="amqp://guest:guest@localhost:5672",
    queue_name="taskiq_queue",
    exchange_name="taskiq_exchange",
    declare_exchange=True,
)
