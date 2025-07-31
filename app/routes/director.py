import logging
from typing import Any, Optional

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select

from app.db.enums import Status
from app.db.session import AsyncSessionLocal
from app.db.user import User
from app.keyboards.main_menu import menu
from app.repositories import stats_repo, task_repo

router = Router()
logger = logging.getLogger(__name__)


# ─────────── FSM ───────────
class AddTask(StatesGroup):
    waiting_title = State()
    waiting_description = State()
    waiting_deadline = State()


# helper: get current user
async def me(tg_id: int) -> Any:
    async with AsyncSessionLocal() as s:
        return await s.scalar(select(User).where(User.tg_id == tg_id))


# ─────────── KPI ───────────
@router.message(Command("kpi"))
async def kpi_cmd(msg: Message) -> None:
    try:
        user = await me(msg.from_user.id)
        if not user or user.role not in ["director", "super"]:
            await msg.answer("Команда доступна только директору.")
            return

        stats = await stats_repo.kpi_summary()

        kpi_text = (
            "📊 <b>KPI Отчет</b>\n\n"
            f"📝 <b>Заметки:</b> {stats['notes_total']}\n"
            f"📋 <b>Заявки:</b> {stats['tickets_total']} (выполнено: {stats['tickets_done']})\n"
            f"📋 <b>Задачи:</b> {stats['tasks_total']} (выполнено: {stats['tasks_done']})\n"
            f"⚠️ <b>Просрочено:</b> {stats['overdue']}\n\n"
            f"📈 <b>Эффективность:</b>\n"
            f"• Заявки: {stats['tickets_done']}/{stats['tickets_total']} "
            f"({stats['tickets_done']/stats['tickets_total']*100:.1f}%)\n"
            f"• Задачи: {stats['tasks_done']}/{stats['tasks_total']} "
            f"({stats['tasks_done']/stats['tasks_total']*100:.1f}%)"
        )

        await msg.answer(kpi_text, reply_markup=menu("director", "ru"))
    except Exception as e:
        logger.error(f"Ошибка при получении KPI: {e}")
        await msg.answer("Произошла ошибка при получении KPI")


# ─────────── Задачи ───────────
@router.callback_query(F.data == "director_tasks")
async def view_tasks(call: CallbackQuery) -> None:
    try:
        user = await me(call.from_user.id)
        if not user or user.role not in ["director", "super"]:
            await call.answer("Доступ запрещен", show_alert=True)
            return

        tasks = await task_repo.list_open()
        if not tasks:
            txt = "📋 <b>Задачи директора</b>\n\nНет активных задач"
        else:
            ico = {Status.open: "🟡", Status.in_progress: "🔵", Status.done: "🟢"}
            txt = "📋 <b>Задачи директора</b>\n\n" + "\n".join(
                f"{ico[t.status]} <b>#{t.id}</b> — {t.title}\n"  # type: ignore
                f"📝 {t.description}\n"
                f"⏰ Дедлайн: {t.deadline.strftime('%d.%m.%Y') if t.deadline else 'Не установлен'}"
                for t in tasks
            )
        if call.message is not None and hasattr(call.message, 'edit_text'):
            await call.message.edit_text(txt, reply_markup=menu("director", "ru"))
        await call.answer()
    except Exception as e:
        logger.error(f"Ошибка при получении задач: {e}")
        await call.answer("Произошла ошибка", show_alert=True)


@router.callback_query(F.data == "director_add_task")
async def start_add_task(call: CallbackQuery, state: Any) -> None:
    try:
        user = await me(call.from_user.id)
        if not user or user.role not in ["director", "super"]:
            await call.answer("Доступ запрещен", show_alert=True)
            return

        await state.set_state(AddTask.waiting_title)
        if call.message is not None and hasattr(call.message, 'edit_text'):
            await call.message.edit_text("📋 <b>Добавление задачи</b>\n\n" "Введите название задачи:")
        await call.answer()
    except Exception as e:
        logger.error(f"Ошибка при начале добавления задачи: {e}")
        await call.answer("Произошла ошибка", show_alert=True)


@router.message(AddTask.waiting_title, F.text)
async def task_title(msg: Message, state: Any) -> None:
    try:
        if msg.text is None:
            await msg.answer("Пожалуйста, введите название задачи.")
            return
        title = msg.text.strip()
        if len(title) > 200:
            await msg.answer("Название задачи слишком длинное (максимум 200 символов)")
            return

        if not title:
            await msg.answer("Название задачи не может быть пустым")
            return

        await state.update_data(title=title)
        await state.set_state(AddTask.waiting_description)
        await msg.answer("Введите описание задачи:")
    except Exception as e:
        logger.error(f"Ошибка при обработке названия задачи: {e}")
        await msg.answer("Произошла ошибка")
        await state.clear()


@router.message(AddTask.waiting_description, F.text)
async def task_description(msg: Message, state: Any) -> None:
    try:
        if msg.text is None:
            await msg.answer("Пожалуйста, введите описание задачи.")
            return
        description = msg.text.strip()
        if len(description) > 1000:
            await msg.answer("Описание задачи слишком длинное (максимум 1000 символов)")
            return

        if not description:
            await msg.answer("Описание задачи не может быть пустым")
            return

        await state.update_data(description=description)
        await state.set_state(AddTask.waiting_deadline)
        await msg.answer("Введите дедлайн в формате ДД.ММ.ГГГГ (или напишите «Нет»):")
    except Exception as e:
        logger.error(f"Ошибка при обработке описания задачи: {e}")
        await msg.answer("Произошла ошибка")
        await state.clear()


@router.message(AddTask.waiting_deadline, F.text)
async def task_deadline(msg: Message, state: Any) -> None:
    try:
        if msg.text is None:
            await msg.answer("Пожалуйста, введите дедлайн.")
            return
        deadline_text = msg.text.strip()

        if deadline_text.lower() == "нет":
            deadline = None
        else:
            try:
                from datetime import datetime

                deadline = datetime.strptime(deadline_text, "%d.%m.%Y").date()
            except ValueError:
                await msg.answer("Пожалуйста, введите дату в формате ДД.ММ.ГГГГ или напишите «Нет»")
                return

        data = await state.get_data()
        user = await me(msg.from_user.id)
        if not user or user.role not in ["director", "super"]:
            await msg.answer("Доступ запрещен")
            await state.clear()
            return

        await task_repo.create_task(
            title=data["title"],
            description=data["description"],
            deadline=deadline,
            author_id=user.id,
        )

        await state.clear()
        await msg.answer("✅ Задача создана!", reply_markup=menu("director", "ru"))
    except Exception as e:
        logger.error(f"Ошибка при создании задачи: {e}")
        await msg.answer("Произошла ошибка при создании задачи")
        await state.clear()


@router.callback_query(lambda c: c.data.startswith(("task_done", "task_prog")))
async def change_task_status(call: CallbackQuery):
    try:
        user = await me(call.from_user.id)
        if not user or user.role not in ["director", "super"]:
            await call.answer("Доступ запрещен", show_alert=True)
            return

        if call.data is None:
            await call.answer("Ошибка данных", show_alert=True)
            return
        task_id = int(call.data.split("_")[-1])
        status = Status.done if call.data.startswith("task_done") else Status.in_progress

        success = await task_repo.set_status(task_id, status)
        if success:
            await call.answer("Статус обновлен", show_alert=True)
            # Обновляем список задач
            tasks = await task_repo.list_open()
            ico = {Status.open: "🟡", Status.in_progress: "🔵", Status.done: "🟢"}
            txt = "📋 <b>Задачи директора</b>\n\n" + "\n".join(
                f"{ico[t.status]} <b>#{t.id}</b> — {t.title}\n"  # type: ignore
                f"📝 {t.description}\n"
                f"⏰ Дедлайн: {t.deadline.strftime('%d.%m.%Y') if t.deadline else 'Не установлен'}"
                for t in tasks
            )
            if call.message is not None and hasattr(call.message, 'edit_text'):
                await call.message.edit_text(txt, reply_markup=menu("director", "ru"))
        else:
            await call.answer("Ошибка обновления статуса", show_alert=True)
    except Exception as e:
        logger.error(f"Ошибка при изменении статуса задачи: {e}")
        await call.answer("Произошла ошибка", show_alert=True)
