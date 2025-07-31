from typing import Any

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select, update

from app.db.session import AsyncSessionLocal
from app.db.user import User
from app.i18n import t
from app.keyboards.main_menu import menu

router = Router()


async def get_user(tg_id: int) -> Any:
    """Получить пользователя по Telegram ID"""
    async with AsyncSessionLocal() as s:
        return await s.scalar(select(User).where(User.tg_id == tg_id))


async def toggle_theme(uid: int) -> str:
    """Переключить тему пользователя"""
    async with AsyncSessionLocal() as s:
        user = await s.scalar(select(User).where(User.tg_id == uid))
        if not user:
            return "light"  # дефолт для неавторизованных

        new = "dark" if user.theme == "light" else "light"
        await s.execute(update(User).where(User.id == user.id).values(theme=new))
        await s.commit()
        return new


@router.message(Command("theme"))
async def cmd_theme(msg: Message, lang: str) -> None:
    """Команда /theme для переключения темы"""
    new = await toggle_theme(msg.from_user.id)
    user = await get_user(msg.from_user.id)

    if user:
        await msg.answer(
            t("common.theme_switched", lang),
            reply_markup=menu(user.role, lang, theme=new),
        )
    else:
        await msg.answer(t("common.theme_switched", lang))


@router.callback_query(lambda c: c.data == "switch_theme")
async def cb_theme(call: CallbackQuery, lang: str) -> None:
    """Кнопка переключения темы"""
    new = await toggle_theme(call.from_user.id)
    user = await get_user(call.from_user.id)

    if user and call.message is not None:
        await call.message.edit_reply_markup(menu(user.role, lang, theme=new))
    await call.answer(t("common.theme_switched", lang))
