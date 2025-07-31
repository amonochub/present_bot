import html
import secrets

from aiogram.fsm.storage.base import StorageKey

CSRF_KEY = "csrf"


async def issue_nonce(storage, chat_id, user_id) -> str:
    nonce = secrets.token_hex(6)
    await storage.set_data(StorageKey(chat_id, user_id), {CSRF_KEY: nonce})
    return nonce


async def check_nonce(storage, chat_id, user_id, nonce: str) -> bool:
    data = await storage.get_data(StorageKey(chat_id, user_id))
    return nonce and data.get(CSRF_KEY) == nonce


def escape_html(text: str) -> str:
    """Экранирует HTML-символы для безопасного отображения"""
    return html.escape(text, quote=True)
