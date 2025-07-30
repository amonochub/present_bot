"""
Middleware для улучшения пользовательского опыта
"""
from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject
from app.i18n import t
import logging
from typing import Any, Awaitable, Callable

log = logging.getLogger(__name__)


class UnknownCommandMiddleware(BaseMiddleware):
    """Middleware для обработки неизвестных команд"""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any]
    ) -> Any:
        try:
            return await handler(event, data)
        except Exception as e:
            lang = data.get("lang", "ru")
            await event.answer(t("common.error_generic", lang))
            log.exception("Unhandled exception in handler")
            return


class FallbackMiddleware(BaseMiddleware):
    """Middleware для обработки неизвестных команд"""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any]
    ) -> Any:
        if isinstance(event, Message) and event.text and event.text.startswith("/"):
            # Проверяем, что это не известная команда
            known_commands = ["/start", "/help", "/notes", "/addnote", "/ticket", "/crash"]
            command = event.text.split()[0].lower()
            
            if command not in known_commands:
                # Неизвестная команда
                lang = data.get("lang", "ru")
                await event.answer(t("common.unknown_cmd", lang))
                return
        
        return await handler(event, data) 