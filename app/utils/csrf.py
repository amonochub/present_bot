import html
import secrets
from typing import Any

from aiogram.fsm.storage.base import StorageKey

CSRF_KEY = "csrf"


async def issue_nonce(storage: Any, chat_id: int, user_id: int) -> str:
    nonce = secrets.token_hex(6)
    await storage.set_data(
        StorageKey(bot_id=0, chat_id=chat_id, user_id=user_id),
        {CSRF_KEY: nonce},
    )
    return nonce


async def check_nonce(storage: Any, chat_id: int, user_id: int, nonce: str) -> bool:
    data = await storage.get_data(StorageKey(bot_id=0, chat_id=chat_id, user_id=user_id))
    return bool(nonce and data.get(CSRF_KEY) == nonce)


def escape_html(text: str) -> str:
    """Экранирует HTML-символы для безопасного отображения"""
    return html.escape(text, quote=True)
