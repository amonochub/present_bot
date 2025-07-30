from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from typing import Any, Awaitable, Callable


class LocaleMiddleware(BaseMiddleware):
    """Middleware для автоматического определения языка пользователя"""
    
    def __init__(self, default: str = "ru"):
        self.default = default
        super().__init__()

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any]
    ) -> Any:
        # Получаем язык из профиля Telegram пользователя
        if hasattr(event, 'from_user') and event.from_user:
            lang = getattr(event.from_user, "language_code", self.default)
            # Поддерживаем только ru и en
            if lang not in ("ru", "en"):
                lang = self.default
        else:
            lang = self.default
        
        # Добавляем язык в контекст
        data["lang"] = lang
        
        return await handler(event, data) 