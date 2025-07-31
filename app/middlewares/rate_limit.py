from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import Message

from app.i18n import t
from app.services.limiter import hit


class RateLimitMiddleware(BaseMiddleware):
    def __init__(self, limit=20, window=60):
        self.limit = limit
        self.window = window

    async def __call__(self, handler: Any, event: Any, data: Any) -> Any:
        if isinstance(event, Message):
            res = await hit(f"rl:{event.from_user.id}", self.limit, self.window)
            if not res.allowed:
                lang = data.get("lang", "ru")
                await event.answer(t("common.rate_limited", lang))
                return
        return await handler(event, data)
