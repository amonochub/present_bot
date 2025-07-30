"""
Хэндлер для команды /help
"""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.db.user import User
from app.i18n import t

router = Router()


async def role_of(tg_id: int) -> str:
    """Получить роль пользователя"""
    async with AsyncSessionLocal() as s:
        result = await s.scalar(select(User.role).where(User.tg_id == tg_id))
        return result or "student"


@router.message(Command("help"))
async def help_cmd(msg: Message, lang: str):
    """Показать справку в зависимости от роли пользователя"""
    role = await role_of(msg.from_user.id)
    txt = t("common.help_header", lang) + "\n\n" + t(f"help.{role}", lang)
    await msg.answer(txt)
