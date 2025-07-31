from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery

from app.utils.csrf import check_nonce


class CSRFMiddleware(BaseMiddleware):
    async def __call__(self, handler: Any, event: Any, data: Any) -> Any:
        if isinstance(event, CallbackQuery):
            if event.data is None:
                await event.answer("⛔️ Ошибка данных.", show_alert=True)
                return
            try:
                nonce, real_data = event.data.split(":", 1)
            except ValueError:  # нет токена
                await event.answer("⛔️ Истекла сессия, войдите заново.", show_alert=True)
                return
            if event.message is None:
                await event.answer("⛔️ Ошибка сообщения.", show_alert=True)
                return
            ok = await check_nonce(
                data["dp"].storage, event.message.chat.id, event.from_user.id, nonce
            )
            if not ok:
                await event.answer("⚠️ Неверный токен.", show_alert=True)
                return
            event.data = real_data  # подменяем для хэндлеров
        return await handler(event, data)
