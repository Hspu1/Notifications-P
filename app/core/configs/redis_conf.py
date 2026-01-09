from redis.asyncio import Redis


class RedisConfig:
    def __init__(self, redis_client: Redis, namespace: str = "translator"):
        self._redis = redis_client
        self._namespace = namespace

    def _get_safe_key(self, not_safe_key: str) -> str:
        return f"{self._namespace}:{not_safe_key}"

    async def get(self, key: str) -> str | None:
        safe_key = self._get_safe_key(not_safe_key=key)
        return await self._redis.get(safe_key)

    async def set(self, key: str, value: str, ex: int) -> None:
        safe_key = self._get_safe_key(not_safe_key=key)
        await self._redis.set(safe_key, value, ex=ex)

    async def aclose(self) -> None:
        await self._redis.aclose()


redis_client = Redis(host="127.0.0.1", port=6379, decode_responses=True, db=3)
redis = RedisConfig(redis_client)
