from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from aiogram.fsm.state import StatesGroup, State
from typing import Optional
import logging
from app.keyboards.main_menu import menu
from app.repositories import ticket_repo, user_repo, media_repo
from app.services import notifier
from app.roles import ROLES
from app.db.user import User
from app.db.session import AsyncSessionLocal
from app.db.enums import Status
from sqlalchemy import select

router = Router()
logger = logging.getLogger(__name__)

# ─────────── FSM для рассылки ───────────
class BroadcastFSM(StatesGroup):
    waiting_text = State()

async def get_user_role(tg_id: int) -> Optional[str]:
    """Получить роль пользователя"""
    async with AsyncSessionLocal() as s:
        user = await s.scalar(select(User).where(User.tg_id == tg_id))
        return user.role if user else None

def ticket_lines(tickets):
    ico = {Status.open: "🟡", Status.in_progress: "🔵", Status.done: "🟢"}
    lines = []
    for t in tickets:
        lines.append(f"{ico[t.status]} <b>#{t.id}</b> — {t.title}")
    return "\n".join(lines) or "Пока нет заявок."

@router.callback_query(F.data == "admin_tickets")
async def view_tickets(call: CallbackQuery):
    try:
        user_role = await get_user_role(call.from_user.id)
        if user_role not in ["admin", "super"]:
            await call.answer("Доступ запрещен", show_alert=True)
            return
            
        tickets = await ticket_repo.list_all()
        txt = "🗂 <b>Заявки учителей</b>\n\n" + ticket_lines(tickets)
        kb = [
            [InlineKeyboardButton("🔄 Обновить", callback_data="admin_tickets")],
            [InlineKeyboardButton("✅ Закрыть #", callback_data="mark_done")],
            [InlineKeyboardButton("🔵 В работу #", callback_data="mark_prog")],
        ]
        await call.message.edit_text(txt,
                                     reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))
        await call.answer()
    except Exception as e:
        logger.error(f"Ошибка при получении тикетов: {e}")
        await call.answer("Произошла ошибка", show_alert=True)

# смена статуса
@router.callback_query(lambda c: c.data.startswith(("mark_done","mark_prog")))
async def change_status(call: CallbackQuery):
    try:
        user_role = await get_user_role(call.from_user.id)
        if user_role not in ["admin", "super"]:
            await call.answer("Доступ запрещен", show_alert=True)
            return
            
        parts = call.data.split()
        if len(parts) != 2 or not parts[1].isdigit():
            await call.answer("После кнопки напишите номер заявки в сообщении.")
            return
        ticket_id = int(parts[1])
        status = Status.done if call.data.startswith("mark_done") else Status.in_progress
        await ticket_repo.set_status(ticket_id, status)
        await call.answer("Статус обновлён!")
        # перерисовать список
        await view_tickets(call)
    except Exception as e:
        logger.error(f"Ошибка при изменении статуса тикета: {e}")
        await call.answer("Произошла ошибка", show_alert=True)

# ─────────── Рассылка ───────────
# кнопка «📢 Рассылка»
@router.callback_query(F.data == "admin_broadcast")
async def start_broadcast(call: CallbackQuery, state):
    user_role = await get_user_role(call.from_user.id)
    if user_role not in ["admin", "super"]:
        await call.answer("Доступ запрещен", show_alert=True)
        return
        
    await state.set_state(BroadcastFSM.waiting_text)
    await call.message.edit_text(
        "📝 <b>Текст рассылки учителям</b>\n"
        "Отправьте сообщение, которым хотите поделиться.")
    await call.answer()

# получаем текст и рассылаем
@router.message(BroadcastFSM.waiting_text, F.text)
async def send_broadcast(msg: Message, state):
    try:
        user_role = await get_user_role(msg.from_user.id)
        if user_role not in ["admin", "super"]:
            await msg.answer("Доступ запрещен")
            await state.clear()
            return
            
        await state.clear()
        ids = await user_repo.teacher_ids()
        count = await notifier.broadcast(ids, f"📢 <b>Сообщение администрации</b>\n\n{msg.text}")
        await msg.answer(f"✅ Разослано {count} учителям.", reply_markup=menu("admin"))
    except Exception as e:
        logger.error(f"Ошибка при рассылке: {e}")
        await msg.answer("Произошла ошибка при рассылке")
        await state.clear()

# ─────────── Медиацентр ───────────
@router.callback_query(F.data == "admin_media")
async def admin_media(call: CallbackQuery):
    try:
        user_role = await get_user_role(call.from_user.id)
        if user_role not in ["admin", "super"]:
            await call.answer("Доступ запрещен", show_alert=True)
            return
            
        reqs = await media_repo.media_list()
        ico = {Status.open: "🟠", Status.in_progress: "🟡", Status.done: "🟢"}
        txt = "🎬 <b>Заявки в медиацентр</b>\n\n" + (
            "\n".join(f"{ico[r.status]} #{r.id} на {r.event_date:%d.%m} — {r.comment}"
                      for r in reqs) or "Пока нет заявок.")
        await call.message.edit_text(txt, reply_markup=menu("admin"))
        await call.answer()
    except Exception as e:
        logger.error(f"Ошибка при получении медиа-заявок: {e}")
        await call.answer("Произошла ошибка", show_alert=True) 