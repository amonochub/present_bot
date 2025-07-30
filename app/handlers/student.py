import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.db.user import User
from app.repositories import psych_repo

router = Router()
logger = logging.getLogger(__name__)


async def get_user_role(tg_id: int) -> str | None:
    """Получить роль пользователя"""
    async with AsyncSessionLocal() as s:
        user = await s.scalar(select(User).where(User.tg_id == tg_id))
        return user.role if user else None


# пункт меню «🆘 Психолог»
@router.callback_query(F.data == "stu_help")
async def ask_help(call: CallbackQuery, lang: str):
    # Проверяем роль пользователя
    user_role = await get_user_role(call.from_user.id)
    if user_role not in ["student", "super"]:
        await call.answer("Эта функция доступна только ученикам", show_alert=True)
        return

    await call.message.edit_text(
        "🧑‍⚕️ *Психологическая помощь*\n"
        "Отправьте текст или голосовое сообщение.\n"
        "Ваше обращение увидит только школьный психолог.",
        parse_mode="Markdown",
    )
    # FSM не требуется: любое следующее сообщение — обращение
    await call.answer()


# ловим текст/voice
@router.message(F.content_type.in_({"voice", "text"}))
async def receive_help(msg: Message, lang: str):
    # Проверяем роль пользователя
    user_role = await get_user_role(msg.from_user.id)
    if user_role not in ["student", "super"]:
        await msg.answer("Эта функция доступна только ученикам")
        return

    try:
        if msg.voice or msg.text:
            file_id = msg.voice.file_id if msg.voice else None
            text = msg.text.strip() if msg.text else None
            await psych_repo.create(msg.from_user.id, text, file_id)
            await msg.answer("✅ Обращение направлено психологу. Спасибо за доверие!")
        else:
            await msg.answer("Пожалуйста, отправьте текст или голосовое сообщение.")
    except Exception as e:
        logger.error(f"Ошибка при создании обращения к психологу: {e}")
        await msg.answer("Произошла ошибка при отправке обращения. Попробуйте позже.")
