import logging
from typing import Optional

from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.db.user import User
from app.keyboards.main_menu import menu
from app.repositories import task_repo
from app.services.pdf_factory import generate_certificate

router = Router()
logger = logging.getLogger(__name__)


# helper: get current user role
async def get_user_role(tg_id: int) -> Optional[str]:
    async with AsyncSessionLocal() as s:
        user = await s.scalar(select(User).where(User.tg_id == tg_id))
        return user.role if user else None


# ─────────── Задания ребенка ───────────
@router.callback_query(F.data == "parent_tasks")
async def view_child_tasks(call: CallbackQuery):
    try:
        user_role = await get_user_role(call.from_user.id)
        if user_role not in ["parent", "super"]:
            await call.answer("Эта функция доступна только родителям", show_alert=True)
            return

        tasks = await task_repo.list_open()
        if not tasks:
            txt = "📚 <b>Задания ребенка</b>\n\nНет активных заданий"
        else:
            txt = "📚 <b>Задания ребенка</b>\n\n" + "\n".join(
                f"📝 <b>{t.title}</b>\n"
                f"📄 {t.description}\n"
                f"⏰ Дедлайн: {t.deadline.strftime('%d.%m.%Y') if t.deadline else 'Не установлен'}\n"
                for t in tasks[:3]  # Показываем только первые 3 задания
            )
            if len(tasks) > 3:
                txt += f"\n... и еще {len(tasks) - 3} заданий"

        await call.message.edit_text(txt, reply_markup=menu("parent", "ru"))
        await call.answer()
    except Exception as e:
        logger.error(f"Ошибка при получении заданий ребенка: {e}")
        await call.answer("Произошла ошибка", show_alert=True)


# ─────────── Справки ───────────
@router.callback_query(F.data == "parent_cert")
async def request_certificate(call: CallbackQuery):
    try:
        user_role = await get_user_role(call.from_user.id)
        if user_role not in ["parent", "super"]:
            await call.answer("Эта функция доступна только родителям", show_alert=True)
            return

        await call.message.edit_text(
            "📄 <b>Запрос справки</b>\n\n" "Выберите тип справки:",
            reply_markup=menu("parent", "ru"),
        )
        await call.answer()
    except Exception as e:
        logger.error(f"Ошибка при запросе справки: {e}")
        await call.answer("Произошла ошибка", show_alert=True)


@router.callback_query(F.data == "cert_attendance")
async def generate_attendance_cert(call: CallbackQuery):
    try:
        user_role = await get_user_role(call.from_user.id)
        if user_role not in ["parent", "super"]:
            await call.answer("Эта функция доступна только родителям", show_alert=True)
            return

        # Генерируем справку о посещаемости
        pdf_data = await generate_certificate(
            cert_type="attendance",
            student_name="Иванов Иван",
            parent_name=call.from_user.full_name,
            date="2024-12-19",
        )

        await call.message.answer_document(
            document=pdf_data,
            caption="📄 Справка о посещаемости\n\n"
            "Справка сгенерирована автоматически.\n"
            "Для получения официальной справки обратитесь в секретариат.",
        )
        await call.answer()
    except Exception as e:
        logger.error(f"Ошибка при генерации справки о посещаемости: {e}")
        await call.answer("Произошла ошибка при генерации справки", show_alert=True)


@router.callback_query(F.data == "cert_progress")
async def generate_progress_cert(call: CallbackQuery):
    try:
        user_role = await get_user_role(call.from_user.id)
        if user_role not in ["parent", "super"]:
            await call.answer("Эта функция доступна только родителям", show_alert=True)
            return

        # Генерируем справку об успеваемости
        pdf_data = await generate_certificate(
            cert_type="progress",
            student_name="Иванов Иван",
            parent_name=call.from_user.full_name,
            date="2024-12-19",
        )

        await call.message.answer_document(
            document=pdf_data,
            caption="📄 Справка об успеваемости\n\n"
            "Справка сгенерирована автоматически.\n"
            "Для получения официальной справки обратитесь в секретариат.",
        )
        await call.answer()
    except Exception as e:
        logger.error(f"Ошибка при генерации справки об успеваемости: {e}")
        await call.answer("Произошла ошибка при генерации справки", show_alert=True)


@router.callback_query(F.data == "cert_behavior")
async def generate_behavior_cert(call: CallbackQuery):
    try:
        user_role = await get_user_role(call.from_user.id)
        if user_role not in ["parent", "super"]:
            await call.answer("Эта функция доступна только родителям", show_alert=True)
            return

        # Генерируем справку о поведении
        pdf_data = await generate_certificate(
            cert_type="behavior",
            student_name="Иванов Иван",
            parent_name=call.from_user.full_name,
            date="2024-12-19",
        )

        await call.message.answer_document(
            document=pdf_data,
            caption="📄 Справка о поведении\n\n"
            "Справка сгенерирована автоматически.\n"
            "Для получения официальной справки обратитесь в секретариат.",
        )
        await call.answer()
    except Exception as e:
        logger.error(f"Ошибка при генерации справки о поведении: {e}")
        await call.answer("Произошла ошибка при генерации справки", show_alert=True)
