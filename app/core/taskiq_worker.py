import asyncio
from app.core.taskiq_broker import setup_broker


async def create_worker_broker():
    return await setup_broker()

# taskiq worker app.core.taskiq_worker:broker --fs-discover --tasks-pattern="app/google_mailing/send_email.py"
broker = asyncio.run(create_worker_broker())
