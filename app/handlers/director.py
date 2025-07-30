import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select

from app.db.enums import Status
from app.db.session import AsyncSessionLocal
from app.db.user import User
from app.keyboards.director import tasks_board
from app.keyboards.main_menu import menu
from app.repositories import stats_repo, task_repo

router = Router()
logger = logging.getLogger(__name__)


# helper — получить роль пользователя
async def me(tg_id: int) -> User | None:
    async with AsyncSessionLocal() as s:
        return await s.scalar(select(User).where(User.tg_id == tg_id))


# /kpi команда
@router.message(Command("kpi"))
async def kpi_cmd(msg: Message):
    try:
        user = await me(msg.from_user.id)
        if user.role not in ("director", "super"):
            await msg.answer("Команда доступна только директору.")
            return

        kpi = await stats_repo.kpi_summary()
        # проценты
        t_done_pct = kpi["tickets_done"] / kpi["tickets_total"] * 100 if kpi["tickets_total"] else 0
        task_done_pct = kpi["tasks_done"] / kpi["tasks_total"] * 100 if kpi["tasks_total"] else 0

        text = (
            "📊 <b>Школьный KPI-отчёт</b>\n\n"
            f"📝 Заметок учителей: <b>{kpi['notes_total']}</b>\n"
            f"🛠 Заявки IT:       <b>{kpi['tickets_done']}/{kpi['tickets_total']}</b> "
            f"({t_done_pct:.0f} %)\n"
            f"⏱ Поручения:       <b>{kpi['tasks_done']}/{kpi['tasks_total']}</b> "
            f"({task_done_pct:.0f} %)\n"
            f"⌛️ Просрочено:      <b>{kpi['overdue']}</b>\n\n"
            f"📈 <a href='http://localhost:3000'>Grafana дашборд</a>"
        )
        await msg.answer(text, reply_markup=menu(user.role, "ru", user.theme))
    except Exception as e:
        logger.error(f"Ошибка при получении KPI: {e}")
        await msg.answer("Произошла ошибка при получении KPI")


# кнопка в демо-меню тоже может вызывать /kpi
@router.callback_query(F.data == "stub", lambda c: c.message.text == "/kpi")
async def stub_kpi(call: CallbackQuery):
    await kpi_cmd(call.message)
    await call.answer()


# Просмотр поручений
@router.callback_query(F.data == "director_tasks")
async def view_tasks(call: CallbackQuery, lang: str):
    try:
        user = await me(call.from_user.id)
        if user.role not in ("director", "super"):
            await call.answer("Доступ запрещен", show_alert=True)
            return

        tasks = await task_repo.list_open()
        await call.message.edit_text("⏱ <b>Поручения</b>", reply_markup=tasks_board(tasks, lang))
    except Exception as e:
        logger.error(f"Ошибка при получении поручений: {e}")
        await call.answer("Произошла ошибка", show_alert=True)


# Переключение статуса поручения
@router.callback_query(lambda c: c.data.startswith("task_"))
async def toggle_task(call: CallbackQuery):
    try:
        user = await me(call.from_user.id)
        if user.role not in ("director", "super"):
            await call.answer("Доступ запрещен", show_alert=True)
            return

        task_id = int(call.data.split("_")[1])
        await task_repo.set_status(task_id, Status.done)
        await call.answer("✅ Выполнено!")
        await view_tasks(call, "ru")
    except Exception as e:
        logger.error(f"Ошибка при изменении статуса поручения: {e}")
        await call.answer("Произошла ошибка", show_alert=True)


# Команда для тестирования KPI
@router.message(Command("kpi_test"))
async def kpi_test(msg: Message):
    """Тестовая команда для проверки KPI метрик"""
    try:
        user = await me(msg.from_user.id)
        if user.role not in ("director", "super"):
            await msg.answer("Команда доступна только директору.")
            return

        # Получаем текущие метрики
        from app.middlewares.metrics import TASKS_COMPLETED, TASKS_OVERDUE, TASKS_TOTAL

        total = TASKS_TOTAL._value.get()
        done = TASKS_COMPLETED._value.get()
        overdue = TASKS_OVERDUE._value.get()

        text = (
            "📊 <b>Текущие KPI метрики</b>\n\n"
            f"📋 Всего поручений: <b>{total}</b>\n"
            f"✅ Выполнено: <b>{done}</b>\n"
            f"⏰ Просрочено: <b>{overdue}</b>\n\n"
            f"💡 Метрики обновляются каждые 60 секунд"
        )
        await msg.answer(text)
    except Exception as e:
        logger.error(f"Ошибка при тестировании KPI: {e}")
        await msg.answer("Произошла ошибка при получении метрик")
