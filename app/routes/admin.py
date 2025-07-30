from aiogram import F, Router
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from app.keyboards.main_menu import menu
from app.repositories import media_repo, ticket_repo, user_repo
from app.services import notifier

router = Router()


# ─────────── FSM для рассылки ───────────
class BroadcastFSM(StatesGroup):
    waiting_text = State()


def ticket_lines(tickets):
    ico = {"open": "🟡", "in_progress": "🔵", "done": "🟢"}
    lines = []
    for t in tickets:
        lines.append(f"{ico[t.status]} <b>#{t.id}</b> — {t.title}")
    return "\n".join(lines) or "Пока нет заявок."


@router.callback_query(F.data == "admin_tickets")
async def view_tickets(call: CallbackQuery):
    tickets = await ticket_repo.list_all()
    txt = "🗂 <b>Заявки учителей</b>\n\n" + ticket_lines(tickets)
    kb = [
        [InlineKeyboardButton("🔄 Обновить", callback_data="admin_tickets")],
        [InlineKeyboardButton("✅ Закрыть #", callback_data="mark_done")],
        [InlineKeyboardButton("🔵 В работу #", callback_data="mark_prog")],
    ]
    await call.message.edit_text(txt, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))
    await call.answer()


# смена статуса
@router.callback_query(lambda c: c.data.startswith(("mark_done", "mark_prog")))
async def change_status(call: CallbackQuery):
    parts = call.data.split()
    if len(parts) != 2 or not parts[1].isdigit():
        await call.answer("После кнопки напишите номер заявки в сообщении.")
        return
    ticket_id = int(parts[1])
    status = "done" if call.data.startswith("mark_done") else "in_progress"
    await ticket_repo.set_status(ticket_id, status)
    await call.answer("Статус обновлён!")
    # перерисовать список
    await view_tickets(call)


# ─────────── Рассылка ───────────
# кнопка «📢 Рассылка»
@router.callback_query(F.data == "admin_broadcast")
async def start_broadcast(call: CallbackQuery, state):
    await state.set_state(BroadcastFSM.waiting_text)
    await call.message.edit_text(
        "📝 <b>Текст рассылки учителям</b>\n" "Отправьте сообщение, которым хотите поделиться."
    )
    await call.answer()


# получаем текст и рассылаем
@router.message(BroadcastFSM.waiting_text, F.text)
async def send_broadcast(msg: Message, state):
    await state.clear()
    ids = await user_repo.teacher_ids()
    count = await notifier.broadcast(ids, f"📢 <b>Сообщение администрации</b>\n\n{msg.text}")
    await msg.answer(f"✅ Разослано {count} учителям.", reply_markup=menu("admin"))


# ─────────── Медиацентр ───────────
@router.callback_query(F.data == "admin_media")
async def admin_media(call: CallbackQuery):
    reqs = await media_repo.media_list()
    ico = {"open": "🟠", "in_progress": "🟡", "done": "🟢"}
    txt = "🎬 <b>Заявки в медиацентр</b>\n\n" + (
        "\n".join(f"{ico[r.status]} #{r.id} на {r.event_date:%d.%m} — {r.comment}" for r in reqs)
        or "Пока нет заявок."
    )
    await call.message.edit_text(txt, reply_markup=menu("admin"))
    await call.answer()
