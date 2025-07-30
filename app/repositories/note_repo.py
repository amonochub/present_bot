import logging

from sqlalchemy import select

from app.db.note import Note
from app.db.session import AsyncSessionLocal

logger = logging.getLogger(__name__)


async def create_note(teacher_id: int, student: str, text: str) -> None:
    """Создать заметку"""
    try:
        async with AsyncSessionLocal() as s:
            note = Note(teacher_id=teacher_id, student_name=student, text=text)
            s.add(note)
            await s.commit()
    except Exception as e:
        logger.error(f"Ошибка при создании заметки: {e}")
        raise


async def list_notes(teacher_id: int) -> list[Note]:
    """Получить список заметок учителя"""
    try:
        async with AsyncSessionLocal() as s:
            result = await s.scalars(
                select(Note).where(Note.teacher_id == teacher_id).order_by(Note.created_at.desc())
            )
            return list(result)
    except Exception as e:
        logger.error(f"Ошибка при получении заметок: {e}")
        return []
