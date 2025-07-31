import logging
from typing import Any, Optional

from aiogram import F, Router
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select

from app.db.enums import Status
from app.db.session import AsyncSessionLocal
from app.db.user import User
from app.keyboards.main_menu import menu
from app.repositories import media_repo, ticket_repo, user_repo
from app.services.notifier import broadcast

router = Router()
logger = logging.getLogger(__name__)


# ─────────── FSM ───────────
class BroadcastFSM(StatesGroup):
    waiting_text = State()


# helper: get current user
async def get_user_role(tg_id: int) -> Any:
    async with AsyncSessionLocal() as s:
        user = await s.scalar(select(User).where(User.tg_id == tg_id))
        return user.role if user else None


def ticket_lines(tickets: list[Any]) -> str:
    ico = {Status.open: "🟡", Status.in_progress: "🔵", Status.done: "🟢"}
    return "\n".join(f"{ico[t.status]} <b>#{t.id}</b> — {t.title} " for t in tickets)


# ─────────── Заявки ───────────
@router.callback_query(F.data == "admin_tickets")
async def view_tickets(call: CallbackQuery) -> None:
    try:
        user_role = await get_user_role(call.from_user.id)
        if user_role not in ["admin", "super"]:
            await call.answer("Доступ запрещен", show_alert=True)
            return

        tickets = await ticket_repo.list_all()
        if not tickets:
            txt = "📋 <b>Заявки техподдержки</b>\n\nНет активных заявок"
        else:
            txt = "📋 <b>Заявки техподдержки</b>\n\n" + ticket_lines(tickets)
        if call.message is not None and hasattr(call.message, 'edit_text'):
            await call.message.edit_text(txt, reply_markup=menu("admin", "ru"))
        await call.answer()
    except Exception as e:
        logger.error(f"Ошибка при получении заявок: {e}")
        await call.answer("Произошла ошибка", show_alert=True)


@router.callback_query(lambda c: c.data.startswith(("mark_done", "mark_prog")))
async def change_status(call: CallbackQuery) -> None:
    try:
        user_role = await get_user_role(call.from_user.id)
        if user_role not in ["admin", "super"]:
            await call.answer("Доступ запрещен", show_alert=True)
            return

        if call.data is None:
            await call.answer("Ошибка данных", show_alert=True)
            return
        ticket_id = int(call.data.split("_")[-1])
        status = Status.done if call.data.startswith("mark_done") else Status.in_progress

        success = await ticket_repo.set_status(ticket_id, status)
        if success:
            await call.answer("Статус обновлен", show_alert=True)
            # Обновляем список заявок
            tickets = await ticket_repo.list_all()
            txt = "📋 <b>Заявки техподдержки</b>\n\n" + ticket_lines(tickets)
            if call.message is not None and hasattr(call.message, 'edit_text'):
                await call.message.edit_text(txt, reply_markup=menu("admin", "ru"))
        else:
            await call.answer("Ошибка обновления статуса", show_alert=True)
    except Exception as e:
        logger.error(f"Ошибка при изменении статуса тикета: {e}")
        await call.answer("Произошла ошибка", show_alert=True)


# ─────────── Медиа-заявки ───────────
@router.callback_query(F.data == "admin_media")
async def view_media(call: CallbackQuery) -> None:
    try:
        user_role = await get_user_role(call.from_user.id)
        if user_role not in ["admin", "super"]:
            await call.answer("Доступ запрещен", show_alert=True)
            return

        requests = await media_repo.list_all()
        if not requests:
            txt = "📹 <b>Заявки медиацентра</b>\n\nНет активных заявок"
        else:
            ico = {Status.open: "🟡", Status.in_progress: "🔵", Status.done: "🟢"}
            txt = "📹 <b>Заявки медиацентра</b>\n\n" + "\n".join(
                f"{ico[r.status]} <b>#{r.id}</b> — {r.comment} " for r in requests
            )
        if call.message is not None and hasattr(call.message, 'edit_text'):
            await call.message.edit_text(txt, reply_markup=menu("admin", "ru"))
        await call.answer()
    except Exception as e:
        logger.error(f"Ошибка при получении медиа-заявок: {e}")
        await call.answer("Произошла ошибка", show_alert=True)


@router.callback_query(lambda c: c.data.startswith(("media_done", "media_prog")))
async def change_media_status(call: CallbackQuery) -> None:
    try:
        user_role = await get_user_role(call.from_user.id)
        if user_role not in ["admin", "super"]:
            await call.answer("Доступ запрещен", show_alert=True)
            return

        if call.data is None:
            await call.answer("Ошибка данных", show_alert=True)
            return
        req_id = int(call.data.split("_")[-1])
        status = Status.done if call.data.startswith("media_done") else Status.in_progress

        success = await media_repo.set_status(req_id, status)
        if success:
            await call.answer("Статус обновлен", show_alert=True)
            # Обновляем список заявок
            requests = await media_repo.list_all()
            ico = {Status.open: "🟡", Status.in_progress: "🔵", Status.done: "🟢"}
            txt = "📹 <b>Заявки медиацентра</b>\n\n" + "\n".join(
                f"{ico[r.status]} <b>#{r.id}</b> — {r.comment} " for r in requests
            )
            if call.message is not None and hasattr(call.message, 'edit_text'):
                await call.message.edit_text(txt, reply_markup=menu("admin", "ru"))
        else:
            await call.answer("Ошибка обновления статуса", show_alert=True)
    except Exception as e:
        logger.error(f"Ошибка при изменении статуса медиа-заявки: {e}")
        await call.answer("Произошла ошибка", show_alert=True)


# ─────────── Рассылка ───────────
@router.callback_query(F.data == "admin_broadcast")
async def start_broadcast(call: CallbackQuery, state: Any) -> None:
    try:
        user_role = await get_user_role(call.from_user.id)
        if user_role not in ["admin", "super"]:
            await call.answer("Доступ запрещен", show_alert=True)
            return

        await state.set_state(BroadcastFSM.waiting_text)
        if call.message is not None and hasattr(call.message, 'edit_text'):
            await call.message.edit_text(
                "📢 <b>Массовая рассылка</b>\n\n"
                "Введите текст сообщения для рассылки всем пользователям:"
            )
        await call.answer()
    except Exception as e:
        logger.error(f"Ошибка при начале рассылки: {e}")
        await call.answer("Произошла ошибка", show_alert=True)


@router.message(BroadcastFSM.waiting_text, F.text)
async def send_broadcast(msg: Message, state: Any) -> None:
    try:
        user_role = await get_user_role(msg.from_user.id)
        if user_role not in ["admin", "super"]:
            await msg.answer("Доступ запрещен")
            await state.clear()
            return

        if msg.text is None:
            await msg.answer("Пожалуйста, введите текст рассылки.")
            return
        text = msg.text.strip()
        if len(text) > 4000:
            await msg.answer("Текст рассылки слишком длинный (максимум 4000 символов)")
            return

        if not text:
            await msg.answer("Текст рассылки не может быть пустым")
            return

        # Получаем список ID учителей для рассылки
        teacher_ids = await user_repo.teacher_ids()

        if not teacher_ids:
            await msg.answer("Нет пользователей для рассылки")
            await state.clear()
            return

        # Отправляем рассылку
        sent_count = await broadcast(teacher_ids, text)

        await state.clear()
        await msg.answer(
            f"✅ Рассылка отправлена!\n\n"
            f"📊 Статистика:\n"
            f"• Всего получателей: {len(teacher_ids)}\n"
            f"• Успешно отправлено: {sent_count}\n"
            f"• Ошибок: {len(teacher_ids) - sent_count}",
            reply_markup=menu("admin", "ru"),
        )
    except Exception as e:
        logger.error(f"Ошибка при отправке рассылки: {e}")
        await msg.answer("Произошла ошибка при отправке рассылки")
        await state.clear()
