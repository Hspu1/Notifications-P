from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi_limiter import FastAPILimiter

from app.core.configs.redis import redis_client
from app.core.configs.taskiq import broker


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    if not broker.is_worker_process:
        await broker.startup()

    app.state.broker = broker
    await FastAPILimiter.init(redis_client)

    yield

    if not broker.is_worker_process:
        await broker.shutdown()
    await FastAPILimiter.close()
