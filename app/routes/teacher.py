import logging
from datetime import datetime
from typing import Any

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
async def me(tg_id: int) -> Any:
    async with AsyncSessionLocal() as s:
        return await s.scalar(select(User).where(User.tg_id == tg_id))


# 1. список заметок
@router.callback_query(F.data == "teacher_notes")  # type: ignore[misc]
async def teacher_notes(call: CallbackQuery, lang: str) -> None:
    try:
        user = await me(call.from_user.id)
        if (
            not user
            or not hasattr(user, "role")
            or user.role not in ["teacher", "super"]
        ):
            await call.answer("Доступ запрещен", show_alert=True)
            return

        if user is not None and hasattr(user, "id") and user.id is not None:
            notes = await note_repo.list_notes(user.id)
        else:
            notes = []
        if not notes:
            txt = t("teacher.notes_empty", lang)
        else:
            txt = "📝 <b>Мои заметки</b>\n\n" + "\n".join(
                f"• <i>{n.student_name}</i> — {n.text} " for n in notes
            )
        if call.message is not None and hasattr(call.message, "edit_text"):
            await call.message.edit_text(
                txt, reply_markup=menu("teacher", lang)
            )
        await call.answer()
    except Exception as e:
        logger.error(f"Ошибка при получении заметок: {e}")
        await call.answer("Произошла ошибка", show_alert=True)


# 2. кнопка «➕ Добавить заметку»
@router.callback_query(F.data == "teacher_add")  # type: ignore[misc]
async def start_add(call: CallbackQuery, state: Any, lang: str) -> None:
    try:
        user = await me(call.from_user.id)
        if (
            not user
            or not hasattr(user, "role")
            or user.role not in ["teacher", "super"]
        ):
            await call.answer("Доступ запрещен", show_alert=True)
            return

        await state.set_state(AddNote.waiting_text)
        if call.message is not None and hasattr(call.message, "edit_text"):
            await call.message.edit_text(t("teacher.add_note_prompt", lang))
        await call.answer()
    except Exception as e:
        logger.error(f"Ошибка при начале добавления заметки: {e}")
        await call.answer("Произошла ошибка", show_alert=True)


# 3. приём строки, сохранение
@router.message(AddNote.waiting_text, F.text)  # type: ignore[misc]
async def save_note(msg: Message, state: Any, lang: str) -> None:
    try:
        if msg.from_user is None:
            await msg.answer("Доступ запрещен")
            await state.clear()
            return

        user = await me(msg.from_user.id)
        if (
            not user
            or not hasattr(user, "role")
            or user.role not in ["teacher", "super"]
        ):
            await msg.answer("Доступ запрещен")
            await state.clear()
            return

        if msg.text is None:
            await msg.answer("Пожалуйста, введите текст заметки.")
            return
        parts = msg.text.strip().split(maxsplit=2)
        if len(parts) < 2:
            await msg.answer(
                "Пожалуйста, введите в формате: <b>Имя ученика Текст заметки</b>",
                parse_mode="HTML",
            )
            return

        student, text = parts[0], " ".join(parts[1:])
        student = " ".join(student.split())  # Очищаем от лишних пробелов

        if len(text) > 1000:
            await msg.answer(
                "Текст заметки слишком длинный (максимум 1000 символов)"
            )
            return

        if not text.strip():
            await msg.answer("Текст заметки не может быть пустым")
            return

        await note_repo.create_note(user.id, student, text)
        await state.clear()
        await msg.answer(
            t("teacher.note_added", lang), reply_markup=menu("teacher", lang)
        )
    except Exception as e:
        logger.error(f"Ошибка при сохранении заметки: {e}")
        await msg.answer(t("common.error_generic", lang))
        await state.clear()


# ─────────── Заявки IT ───────────
@router.callback_query(F.data == "teacher_ticket")  # type: ignore[misc]
async def start_ticket(call: CallbackQuery, state: Any, lang: str) -> None:
    try:
        user = await me(call.from_user.id)
        if (
            not user
            or not hasattr(user, "role")
            or user.role not in ["teacher", "super"]
        ):
            await call.answer("Доступ запрещен", show_alert=True)
            return

        await state.set_state(AddTicket.waiting_title)
        if call.message is not None and hasattr(call.message, "edit_text"):
            await call.message.edit_text(t("teacher.ticket_text_prompt", lang))
        await call.answer()
    except Exception as e:
        logger.error(f"Ошибка при начале создания заявки: {e}")
        await call.answer("Произошла ошибка", show_alert=True)


@router.message(AddTicket.waiting_title, F.text)  # type: ignore[misc]
async def ticket_title(msg: Message, state: Any, lang: str) -> None:
    try:
        if msg.text is None:
            await msg.answer("Пожалуйста, введите описание заявки.")
            return
        title = msg.text.strip()
        if len(title) > 200:
            await msg.answer(
                "Описание заявки слишком длинное (максимум 200 символов)"
            )
            return

        if not title:
            await msg.answer("Описание заявки не может быть пустым")
            return

        await state.update_data(title=title)
        await state.set_state(AddTicket.waiting_file)
        await msg.answer(
            "Прикрепите фото/файл (опционально) или напишите «Пропустить»:"
        )
    except Exception as e:
        logger.error(f"Ошибка при обработке описания заявки: {e}")
        await msg.answer(t("common.error_generic", lang))
        await state.clear()


@router.message(AddTicket.waiting_file, lambda m: m.document or m.photo or m.text)  # type: ignore[misc]
async def ticket_file(msg: Message, state: Any, lang: str) -> None:
    try:
        data = await state.get_data()
        file_id = None

        if msg.text is not None and msg.text.strip().lower() == "пропустить":
            file_id = None
        elif msg.photo:
            file_id = msg.photo[-1].file_id
        elif msg.document:
            file_id = msg.document.file_id
        else:
            await msg.answer(
                "Пожалуйста, прикрепите файл или напишите «Пропустить»"
            )
            return

        if msg.from_user is None:
            await msg.answer("Доступ запрещен")
            await state.clear()
            return

        user = await me(msg.from_user.id)
        if (
            not user
            or not hasattr(user, "role")
            or user.role not in ["teacher", "super"]
        ):
            await msg.answer("Доступ запрещен")
            await state.clear()
            return

        ticket = await ticket_repo.create_ticket(
            user.id, data["title"], file_id
        )
        await state.clear()
        await msg.answer(
            t("teacher.ticket_created", lang).format(ticket_id=ticket.id),
            reply_markup=menu("teacher", lang),
        )
    except Exception as e:
        logger.error(f"Ошибка при создании заявки: {e}")
        await msg.answer("Произошла ошибка")
        await state.clear()


# ─────────── Медиа-заявки ───────────
@router.callback_query(F.data == "teacher_media")  # type: ignore[misc]
async def media_start(call: CallbackQuery, state: Any, lang: str) -> None:
    try:
        user = await me(call.from_user.id)
        if (
            not user
            or not hasattr(user, "role")
            or user.role not in ["teacher", "super"]
        ):
            await call.answer("Доступ запрещен", show_alert=True)
            return

        await state.set_state(MediaFSM.waiting_date)
        if call.message is not None and hasattr(call.message, "edit_text"):
            await call.message.edit_text(
                "Введите дату мероприятия (например, 25.12.2024):"
            )
        await call.answer()
    except Exception as e:
        logger.error(f"Ошибка при начале создания медиа-заявки: {e}")
        await call.answer("Произошла ошибка", show_alert=True)


@router.message(MediaFSM.waiting_date, F.text)  # type: ignore[misc]
async def media_date(msg: Message, state: Any) -> None:
    try:
        if msg.text is None:
            await msg.answer("Пожалуйста, введите дату мероприятия.")
            return
        date_str = msg.text.strip()
        # Простая валидация даты
        try:
            datetime.strptime(date_str, "%d.%m.%Y")
        except ValueError:
            await msg.answer("Пожалуйста, введите дату в формате ДД.ММ.ГГГГ")
            return

        await state.update_data(date=date_str)
        await state.set_state(MediaFSM.waiting_file)
        await msg.answer("Прикрепите фото/видео для мероприятия:")
    except Exception as e:
        logger.error(f"Ошибка при обработке даты медиа-заявки: {e}")
        await msg.answer("Произошла ошибка")
        await state.clear()


@router.message(MediaFSM.waiting_file, lambda m: m.photo or m.document)  # type: ignore[misc]
async def media_file(msg: Message, state: Any) -> None:
    try:
        file_id = None
        if msg.photo:
            file_id = msg.photo[-1].file_id
        elif msg.document:
            file_id = msg.document.file_id

        await state.update_data(file_id=file_id)
        await state.set_state(MediaFSM.waiting_text)
        await msg.answer("Введите комментарий к заявке:")
    except Exception as e:
        logger.error(f"Ошибка при обработке файла медиа-заявки: {e}")
        await msg.answer("Произошла ошибка")
        await state.clear()


@router.message(MediaFSM.waiting_text, F.text)  # type: ignore[misc]
async def media_finish(msg: Message, state: Any, lang: str) -> None:
    try:
        data = await state.get_data()
        if msg.from_user is None:
            await msg.answer("Доступ запрещен")
            await state.clear()
            return

        user = await me(msg.from_user.id)
        if (
            not user
            or not hasattr(user, "role")
            or user.role not in ["teacher", "super"]
        ):
            await msg.answer("Доступ запрещен")
            await state.clear()
            return

        if msg.text is None:
            await msg.answer("Пожалуйста, введите комментарий.")
            return
        comment = msg.text.strip()
        if len(comment) > 500:
            await msg.answer(
                "Комментарий слишком длинный (максимум 500 символов)"
            )
            return

        await media_repo.create(
            user.id, data["date"], comment, data["file_id"]
        )
        await state.clear()
        await msg.answer(
            "✅ Медиа-заявка создана!", reply_markup=menu("teacher", lang)
        )
    except Exception as e:
        logger.error(f"Ошибка при создании медиа-заявки: {e}")
        await msg.answer("Произошла ошибка")
        await state.clear()
