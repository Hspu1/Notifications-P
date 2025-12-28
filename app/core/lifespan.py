from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.taskiq_broker import broker


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    if not broker.is_worker_process:
        await broker.startup()
    app.state.broker = broker

    yield

    if not broker.is_worker_process:
        await broker.shutdown()
