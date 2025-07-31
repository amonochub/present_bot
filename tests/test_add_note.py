from app.db.note import Note
from app.db.user import User


def test_add_note_functionality():
    """Тест функциональности добавления заметки"""
    # Создаем тестового учителя
    teacher = User(
        tg_id=1001,
        username="test_teacher",
        first_name="Демо",
        last_name="Учитель",
        role="teacher",
        is_active=True,
    )

    # Проверяем, что учитель создан
    assert teacher.tg_id == 1001
    assert teacher.role == "teacher"

    # Создаем заметку
    note = Note(student_name="Петров", text="Петров отлично справился с заданием", teacher_id=1)

    # Проверяем, что заметка создана
    assert note.student_name == "Петров"
    assert note.teacher_id == 1


def test_note_validation():
    """Тест валидации заметки"""
    # Проверяем, что заметка создается с обязательными полями
    note = Note(student_name="Иванов", text="Содержание заметки", teacher_id=1)

    assert note.student_name == "Иванов"
    assert note.text == "Содержание заметки"
    assert note.teacher_id == 1
