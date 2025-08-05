from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

from app.i18n import t
from app.services.limiter import hit


class RateLimitMiddleware(BaseMiddleware):
    def __init__(self, limit: int = 20, window: int = 60) -> None:
        self.limit = limit
        self.window = window

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if isinstance(event, Message):
            if event.from_user is None:
                return await handler(event, data)
            res = await hit(
                f"rl:{event.from_user.id}", self.limit, self.window
            )
            if not res.allowed:
                lang = data.get("lang", "ru")
                await event.answer(t("common.rate_limited", lang))
                return
        return await handler(event, data)
