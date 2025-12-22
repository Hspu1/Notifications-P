from taskiq_aio_pika import AioPikaBroker

# taskiq worker app.core.taskiq_broker:broker --fs-discover --tasks-pattern="app/google_mailing/send_email.py"
broker = AioPikaBroker(
    url="amqp://guest:guest@localhost:5672",
    queue_name="taskiq_queue",  # основная очередь
    exchange_name="taskiq_exchange",  # основной обменник
    declare_queues=True,  # автоматически создаем очередь и обменник
    persistent=True,  # сохраняем сообщение на диск, предотвращая утечку данных
    queue_durable=True,  # очередь выживает при перезапуске
    exchange_durable=True,  # Exchange выживает при перезапуске
    reconnect_on_fail=True,  # Автопереподключение
    prefetch_count=20,  # ограничение параллельной обработки, предотвращая перегрузку воркеров
)
