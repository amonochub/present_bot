"""
Middleware для аудита действий пользователей
"""

import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject
from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.db.user import User

logger = logging.getLogger(__name__)


class AuditMiddleware(BaseMiddleware):
    """Middleware для логирования действий пользователей"""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        # Получаем информацию о пользователе
        user_info = await self._get_user_info(event)

        # Логируем действие
        await self._log_action(event, user_info)

        # Выполняем обработчик
        result = await handler(event, data)

        return result

    async def _get_user_info(self, event: TelegramObject) -> dict[str, Any]:
        """Получить информацию о пользователе"""
        try:
            if hasattr(event, "from_user") and event.from_user:
                async with AsyncSessionLocal() as s:
                    user = await s.scalar(
                        select(User).where(User.tg_id == event.from_user.id)
                    )
                    if user:
                        return {
                            "user_id": user.id,
                            "tg_id": user.tg_id,
                            "role": user.role,
                            "username": user.username,
                            "first_name": user.first_name,
                            "last_name": user.last_name,
                        }
                    else:
                        return {
                            "tg_id": event.from_user.id,
                            "role": "unknown",
                            "username": event.from_user.username,
                            "first_name": event.from_user.first_name,
                            "last_name": event.from_user.last_name,
                        }
        except Exception as e:
            logger.error(f"Ошибка при получении информации о пользователе: {e}")
            return {"error": str(e)}

    async def _log_action(
        self, event: TelegramObject, user_info: dict[str, Any]
    ) -> None:
        """Логировать действие пользователя"""
        try:
            action_type = self._get_action_type(event)
            action_data = self._get_action_data(event)

            log_message = (
                f"AUDIT: User {user_info.get('role', 'unknown')} "
                f"(ID: {user_info.get('user_id', user_info.get('tg_id', 'unknown'))}) "
                f"performed {action_type}: {action_data}"
            )

            # Логируем с разными уровнями в зависимости от типа действия
            if action_type in ["login", "logout", "role_change"]:
                logger.info(log_message)
            elif action_type in ["data_access", "data_modification"]:
                logger.warning(log_message)
            else:
                logger.debug(log_message)

        except Exception as e:
            logger.error(f"Ошибка при логировании действия: {e}")

    def _get_action_type(self, event: TelegramObject) -> str:
        """Определить тип действия"""
        if isinstance(event, Message):
            if event.text and event.text.startswith("/"):
                return "command"
            elif event.text:
                return "message"
            elif event.photo or event.document or event.voice:
                return "file_upload"
        elif isinstance(event, CallbackQuery):
            if event.data.startswith("switch_"):
                return "role_change"
            elif event.data.startswith("admin_") or event.data.startswith("teacher_"):
                return "menu_access"
            else:
                return "button_click"

        return "unknown"

    def _get_action_data(self, event: TelegramObject) -> str:
        """Получить данные действия"""
        if isinstance(event, Message):
            if event.text:
                # Ограничиваем длину для безопасности
                return event.text[:100] + ("..." if len(event.text) > 100 else "")
        elif isinstance(event, CallbackQuery):
            return event.data[:50] + ("..." if len(event.data) > 50 else "")

        return "no_data"
