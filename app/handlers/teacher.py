import logging
from datetime import datetime

from aiogram import F, Router
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.db.user import User
from app.i18n import t
from app.keyboards.main_menu import menu
from app.repositories import media_repo, note_repo, ticket_repo

router = Router()
logger = logging.getLogger(__name__)


# ─────────── FSM ───────────
class AddNote(StatesGroup):
    waiting_text = State()


class AddTicket(StatesGroup):
    waiting_title = State()
    waiting_file = State()


class MediaFSM(StatesGroup):
    waiting_date = State()
    waiting_file = State()
    waiting_text = State()


# helper: get current user
async def me(tg_id: int) -> User | None:
    async with AsyncSessionLocal() as s:
        return await s.scalar(select(User).where(User.tg_id == tg_id))


# 1. список заметок
@router.callback_query(F.data == "teacher_notes")
async def teacher_notes(call: CallbackQuery, lang: str):
    try:
        user = await me(call.from_user.id)
        if not user or user.role not in ["teacher", "super"]:
            await call.answer("Доступ запрещен", show_alert=True)
            return

        notes = await note_repo.list_notes(user.id)
        if not notes:
            txt = t("teacher.notes_empty", lang)
        else:
            txt = "📝 <b>Мои заметки</b>\n\n" + "\n".join(
                f"• <i>{n.student_name}</i> — {n.text} " for n in notes
            )
        await call.message.edit_text(txt, reply_markup=menu("teacher", lang))
        await call.answer()
    except Exception as e:
        logger.error(f"Ошибка при получении заметок: {e}")
        await call.answer("Произошла ошибка", show_alert=True)


# 2. кнопка «➕ Добавить заметку»
@router.callback_query(F.data == "teacher_add")
async def start_add(call: CallbackQuery, state, lang: str):
    user = await me(call.from_user.id)
    if not user or user.role not in ["teacher", "super"]:
        await call.answer("Доступ запрещен", show_alert=True)
        return

    await state.set_state(AddNote.waiting_text)
    await call.message.edit_text(t("teacher.add_note_prompt", lang))
    await call.answer()


# 3. приём строки, сохранение
@router.message(AddNote.waiting_text, F.text)
async def save_note(msg: Message, state, lang: str):
    try:
        user = await me(msg.from_user.id)
        if not user or user.role not in ["teacher", "super"]:
            await msg.answer("Доступ запрещен")
            await state.clear()
            return

        parts = msg.text.strip().split(maxsplit=2)
        if len(parts) < 2:
            await msg.answer(t("common.error_generic", lang))
            return

        student, text = parts[0], " ".join(parts[1:])
        student = " ".join(student.split())  # Очищаем от лишних пробелов

        if len(text) > 1000:
            await msg.answer(t("teacher.note_text_too_long", lang))
            return

        if not text.strip():
            await msg.answer(t("teacher.note_text_empty", lang))
            return

        await note_repo.create_note(user.id, student, text)
        await state.clear()
        await msg.answer(t("teacher.note_added", lang), reply_markup=menu("teacher", lang))
    except Exception as e:
        logger.error(f"Ошибка при сохранении заметки: {e}")
        await msg.answer(t("common.error_generic", lang))
        await state.clear()


# ─────────── Заявки IT ───────────
@router.callback_query(F.data == "teacher_ticket")
async def start_ticket(call: CallbackQuery, state, lang: str):
    user = await me(call.from_user.id)
    if not user or user.role not in ["teacher", "super"]:
        await call.answer("Доступ запрещен", show_alert=True)
        return

    await state.set_state(AddTicket.waiting_title)
    await call.message.edit_text(t("teacher.ticket_text_prompt", lang))
    await call.answer()


@router.message(AddTicket.waiting_title, F.text)
async def ticket_title(msg: Message, state, lang: str):
    if len(msg.text.strip()) > 500:
        await msg.answer(t("teacher.ticket_text_too_long", lang))
        return

    if not msg.text.strip():
        await msg.answer(t("teacher.ticket_text_empty", lang))
        return

    await state.update_data(title=msg.text.strip())
    await state.set_state(AddTicket.waiting_file)
    await msg.answer("Прикрепите фото/файл (опционально) или напишите «Пропустить»:")


@router.message(AddTicket.waiting_file, lambda m: m.document or m.photo or m.text)
async def ticket_file(msg: Message, state, lang: str):
    try:
        data = await state.get_data()
        file_id = None
        if msg.photo:
            file_id = msg.photo[-1].file_id
        elif msg.document:
            file_id = msg.document.file_id

        user = await me(msg.from_user.id)
        if not user or user.role not in ["teacher", "super"]:
            await msg.answer("Доступ запрещен")
            await state.clear()
            return

        ticket = await ticket_repo.create_ticket(user.id, data["title"], file_id)
        await state.clear()
        await msg.answer(
            t("teacher.ticket_created", lang).format(ticket_id=ticket.id),
            reply_markup=menu("teacher", lang),
        )
    except Exception as e:
        logger.error(f"Ошибка при создании тикета: {e}")
        await msg.answer(t("common.error_generic", lang))
        await state.clear()


# ─────────── Медиа-заявки ───────────
@router.callback_query(F.data == "teacher_media")
async def media_start(call: CallbackQuery, state, lang: str):
    user = await me(call.from_user.id)
    if not user or user.role not in ["teacher", "super"]:
        await call.answer("Доступ запрещен", show_alert=True)
        return

    await state.set_state(MediaFSM.waiting_date)
    await call.message.edit_text(
        "📹 <b>Заявка в медиацентр</b>\n" "Введите дату мероприятия в формате ДД.ММ.ГГГГ:"
    )
    await call.answer()


@router.message(MediaFSM.waiting_date, F.text)
async def media_date(msg: Message, state):
    try:
        date_obj = datetime.strptime(msg.text.strip(), "%d.%m.%Y").date()
    except ValueError:
        await msg.answer("Неверный формат. Попробуйте снова (ДД.ММ.ГГГГ):")
        return
    await state.update_data(event_date=date_obj)
    await state.set_state(MediaFSM.waiting_file)
    await msg.answer("Прикрепите фото/плакат или сценарий (файл обязательно):")


@router.message(MediaFSM.waiting_file, lambda m: m.photo or m.document)
async def media_file(msg: Message, state):
    file_id = msg.photo[-1].file_id if msg.photo else msg.document.file_id
    await state.update_data(file_id=file_id)
    await state.set_state(MediaFSM.waiting_text)
    await msg.answer("Добавьте комментарий/сценарий (одной строкой):")


@router.message(MediaFSM.waiting_text, F.text)
async def media_finish(msg: Message, state, lang: str):
    try:
        data = await state.get_data()
        user = await me(msg.from_user.id)
        if not user or user.role not in ["teacher", "super"]:
            await msg.answer("Доступ запрещен")
            await state.clear()
            return

        await media_repo.media_create(
            user.id, data["event_date"], msg.text.strip(), data["file_id"]
        )
        await state.clear()
        await msg.answer("✅ Заявка отправлена в медиацентр!", reply_markup=menu("teacher", lang))
    except Exception as e:
        logger.error(f"Ошибка при создании медиа-заявки: {e}")
        await msg.answer(t("common.error_generic", lang))
        await state.clear()
