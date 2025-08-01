import redis.asyncio as aioredis
from pydantic import BaseModel

from app.config import settings


class LimitResult(BaseModel):
    allowed: bool
    retry_after: int | None = None


redis_client = aioredis.from_url(settings.REDIS_DSN, decode_responses=True)


async def hit(key: str, limit: int, window: int) -> LimitResult:
    """Проверяет rate limit для ключа"""
    ttl = await redis_client.ttl(key)
    val = await redis_client.incr(key)
    if val == 1:
        await redis_client.expire(key, window)
    if val > limit:
        return LimitResult(allowed=False, retry_after=max(ttl, 0))
    return LimitResult(allowed=True)
