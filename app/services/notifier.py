from typing import Iterable
import logging, asyncio
from aiogram import Bot
from app.config import TELEGRAM_TOKEN

log = logging.getLogger(__name__)

async def broadcast(user_ids: Iterable[int], text: str) -> int:
    """
    Отправляет `text` всем Telegram-ID из списка.
    Возвращает количество успешно доставленных сообщений.
    """
    sent = 0
    try:
        async with Bot(TELEGRAM_TOKEN, parse_mode="HTML") as tmp:
            for uid in user_ids:
                try:
                    await tmp.send_message(uid, text)
                    sent += 1
                except Exception as e:
                    log.warning("Не удалось отправить %s: %s", uid, e)
    except Exception as e:
        log.error(f"Ошибка при создании бота для рассылки: {e}")
    return sent 