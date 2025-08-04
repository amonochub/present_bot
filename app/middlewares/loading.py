"""
Middleware для показа индикаторов загрузки
"""

import asyncio
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware, Bot
from aiogram.types import CallbackQuery, Message, TelegramObject


class LoadingMiddleware(BaseMiddleware):
    """Middleware для показа индикаторов загрузки"""

    def __init__(self, bot: Bot, min_delay: float = 0.5):
        super().__init__()
        self.bot = bot
        self.min_delay = min_delay

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        """Обрабатывает событие с показом индикатора загрузки"""

        # Определяем chat_id в зависимости от типа события
        if isinstance(event, Message):
            chat_id: int = event.chat.id
        elif isinstance(event, CallbackQuery):
            chat_id = event.message.chat.id if event.message else None
        else:
            chat_id = None

        if not chat_id:
            return await handler(event, data)

        # Показываем индикатор "бот печатает"
        await self.bot.send_chat_action(chat_id, "typing")

        # Засекаем время начала
        start_time = asyncio.get_event_loop().time()

        try:
            # Выполняем обработчик
            result = await handler(event, data)

            # Вычисляем время выполнения
            execution_time = asyncio.get_event_loop().time() - start_time

            # Если выполнение заняло меньше минимального времени, добавляем задержку
            if execution_time < self.min_delay:
                remaining_delay = self.min_delay - execution_time
                await asyncio.sleep(remaining_delay)

            return result

        except Exception as e:
            # В случае ошибки также показываем индикатор
            await self.bot.send_chat_action(chat_id, "typing")
            await asyncio.sleep(0.3)
            raise e


class LongOperationMiddleware(BaseMiddleware):
    """Middleware для длительных операций"""

    def __init__(self, bot: Bot, threshold: float = 3.0):
        super().__init__()
        self.bot = bot
        self.threshold = threshold

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        """Обрабатывает событие с показом промежуточного сообщения для длительных операций"""

        # Определяем chat_id в зависимости от типа события
        if isinstance(event, Message):
            chat_id: int = event.chat.id
        elif isinstance(event, CallbackQuery):
            chat_id = event.message.chat.id if event.message else None
        else:
            chat_id = None

        if not chat_id:
            return await handler(event, data)

        # Показываем индикатор "бот печатает"
        await self.bot.send_chat_action(chat_id, "typing")

        # Засекаем время начала
        start_time = asyncio.get_event_loop().time()

        # Запускаем обработчик в отдельной задаче
        task: asyncio.Task[Any] = asyncio.create_task(handler(event, data))

        # Ждём пороговое время
        try:
            await asyncio.wait_for(task, timeout=self.threshold)
            return task.result()
        except asyncio.TimeoutError:
            # Если операция занимает больше порогового времени, показываем промежуточное сообщение
            if isinstance(event, Message):
                await event.answer("⏳ Выполняется запрос, это может занять до 10 секунд...")
            elif isinstance(event, CallbackQuery):
                await event.answer("⏳ Обрабатываем запрос...")

            # Ждём завершения операции
            result = await task
            return result
