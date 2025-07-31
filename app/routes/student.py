import logging
from typing import Any, Optional

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.db.user import User
from app.keyboards.main_menu import menu
from app.repositories import psych_repo, task_repo

router = Router()
logger = logging.getLogger(__name__)


# helper: get current user role
async def get_user_role(tg_id: int) -> Any:
    async with AsyncSessionLocal() as s:
        user = await s.scalar(select(User).where(User.tg_id == tg_id))
        return user.role if user else None


# ─────────── Задания ───────────
@router.callback_query(F.data == "stu_tasks")
async def view_tasks(call: CallbackQuery) -> None:
    try:
        user_role = await get_user_role(call.from_user.id)
        if user_role not in ["student", "super"]:
            await call.answer("Эта функция доступна только ученикам", show_alert=True)
            return

        tasks = await task_repo.list_open()
        if not tasks:
            txt = "📚 <b>Задания</b>\n\nНет активных заданий"
        else:
            txt = "📚 <b>Задания</b>\n\n" + "\n".join(
                f"📝 <b>{t.title}</b>\n"
                f"📄 {t.description}\n"
                f"⏰ Дедлайн: "
                f"{t.deadline.strftime('%d.%m.%Y') if t.deadline else 'Не установлен'}\n"
                for t in tasks[:5]  # Показываем только первые 5 заданий
            )
            if len(tasks) > 5:
                txt += f"\n... и еще {len(tasks) - 5} заданий"

        if call.message is not None and hasattr(call.message, 'edit_text'):
            await call.message.edit_text(txt, reply_markup=menu("student", "ru"))
        await call.answer()
    except Exception as e:
        logger.error(f"Ошибка при получении заданий: {e}")
        await call.answer("Произошла ошибка", show_alert=True)


# ─────────── Помощь психолога ───────────
@router.callback_query(F.data == "stu_help")
async def ask_help(call: CallbackQuery, lang: str) -> None:
    try:
        user_role = await get_user_role(call.from_user.id)
        if user_role not in ["student", "super"]:
            await call.answer("Эта функция доступна только ученикам", show_alert=True)
            return

        if call.message is not None and hasattr(call.message, 'edit_text'):
            await call.message.edit_text(
                "💬 <b>Обращение к психологу</b>\n\n"
                "Напишите ваш вопрос или проблему, и психолог ответит вам.\n"
                "Вы также можете отправить голосовое сообщение.",
                reply_markup=menu("student", lang),
            )
        await call.answer()
    except Exception as e:
        logger.error(f"Ошибка при запросе помощи: {e}")
        await call.answer("Произошла ошибка", show_alert=True)


@router.message(F.content_type.in_({"voice", "text"}))
async def receive_help(msg: Message, lang: str) -> None:
    try:
        user_role = await get_user_role(msg.from_user.id)
        if user_role not in ["student", "super"]:
            await msg.answer("Эта функция доступна только ученикам")
            return

        # Получаем текст сообщения
        if msg.voice:
            # Для голосовых сообщений пока просто уведомляем
            text = "Голосовое сообщение"
            await msg.answer(
                "🎤 Голосовые сообщения пока не поддерживаются. "
                "Пожалуйста, напишите ваш вопрос текстом."
            )
            return
        else:
            if msg.text is None:
                await msg.answer("Пожалуйста, напишите ваш вопрос или проблему.")
                return
            text = msg.text.strip()

        if not text:
            await msg.answer("Пожалуйста, напишите ваш вопрос или проблему.")
            return

        if len(text) > 2000:
            await msg.answer("Сообщение слишком длинное (максимум 2000 символов)")
            return

        # Создаем обращение к психологу
        await psych_repo.create(msg.from_user.id, text, None)

        await msg.answer(
            "✅ Ваше обращение отправлено психологу!\n\n"
            "Психолог рассмотрит ваш вопрос и ответит в ближайшее время.",
            reply_markup=menu("student", lang),
        )
    except Exception as e:
        logger.error(f"Ошибка при создании обращения к психологу: {e}")
        await msg.answer("Произошла ошибка при отправке обращения. Попробуйте позже.")
