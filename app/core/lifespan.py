from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.taskiq_broker import setup_broker


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    broker = await setup_broker()

    if not broker.is_worker_process:
        await broker.startup()
    app.state.broker = broker

    yield

    if not broker.is_worker_process:
        await broker.shutdown()
