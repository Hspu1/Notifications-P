from taskiq_aio_pika import AioPikaBroker

# taskiq worker app.core.taskiq_broker:broker --fs-discover --tasks-pattern="app/google_mailing/send_email.py"
# основной воркер
broker = AioPikaBroker(
    url="amqp://guest:guest@localhost:5672",
    queue_name="main_taskiq_queue",  # основная очередь
    exchange_name="main_taskiq_exchange",  # основной обменник
    dead_letter_queue_name="dlq_taskiq_queue",  # dlq очередь
    dead_letter_exchange_name="dlq_taskiq_exchange",  # dlq обменник
    queue_arguments={  # дополнительно для применения настроек
        "x-dead-letter-exchange": "dlq_taskiq_exchange",
        "x-dead-letter-routing-key": "dlq_taskiq_queue"
    },
    declare_queues=True,  # автоматически создаем очередь и обменник
    persistent=True,  # сохраняем сообщение на диск, предотвращая утечку данных
    queue_durable=True,  # очередь выживает при перезапуске
    exchange_durable=True,  # Exchange выживает при перезапуске
    reconnect_on_fail=True,  # Автопереподключение
    prefetch_count=20  # ограничение параллельной обработки, предотвращая перегрузку воркеров
)

# taskiq worker app.core.taskiq_broker:dlq_broker --fs-discover
# доп воркер для реализации dlq
dlq_broker = AioPikaBroker(
    url="amqp://guest:guest@localhost:5672",
    queue_name="dlq_taskiq_queue",  # назначаем основную очередь для этого воркера
    exchange_name="dlq_taskiq_exchange",  # назначаем основной обменник для этого воркера
    declare_queues=True,
    persistent=True,
    queue_durable=True,
    exchange_durable=True,
    reconnect_on_fail=True,
    prefetch_count=20
)
