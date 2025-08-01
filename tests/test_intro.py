from app.db.user import User
from app.routes.intro import INTRO_SLIDES


def test_intro_slides_structure():
    """Тест структуры слайдов онбординга"""
    assert len(INTRO_SLIDES) == 6

    for slide in INTRO_SLIDES:
        assert "title" in slide
        assert "text" in slide
        assert "icon" in slide
        assert isinstance(slide["title"], str)
        assert isinstance(slide["text"], str)
        assert isinstance(slide["icon"], str)


def test_intro_slides_content():
    """Тест содержания слайдов онбординга"""
    # Проверяем, что все роли представлены
    roles = ["Учитель", "Администрация", "Директор", "Ученик", "Родитель", "Психолог"]

    for i, slide in enumerate(INTRO_SLIDES):
        assert any(role in slide["title"] for role in roles)
        assert len(slide["text"]) > 10  # Текст должен быть информативным
        assert slide["icon"] in ["👩‍🏫", "🏛", "📈", "👨‍🎓", "👪", "🧑‍⚕️"]


def test_user_model_with_intro():
    """Тест модели пользователя с полем seen_intro"""
    # Создаем пользователя без онбординга
    user = User(
        tg_id=123456789,
        username="test_user",
        first_name="Тест",
        last_name="Пользователь",
        role="student",
        seen_intro=False,
    )

    assert user.seen_intro is False

    # Создаем пользователя с пройденным онбордингом
    user_with_intro = User(
        tg_id=987654321,
        username="test_user2",
        first_name="Тест2",
        last_name="Пользователь2",
        role="teacher",
        seen_intro=True,
    )

    assert user_with_intro.seen_intro is True


def test_intro_slide_index():
    """Тест индексов слайдов онбординга"""
    # Проверяем, что индексы корректные
    for i in range(len(INTRO_SLIDES)):
        slide = INTRO_SLIDES[i]
        assert slide is not None
        assert "title" in slide
        assert "text" in slide


def test_intro_slides_unique():
    """Тест уникальности слайдов онбординга"""
    titles = [slide["title"] for slide in INTRO_SLIDES]
    assert len(titles) == len(set(titles))  # Все заголовки уникальны

    icons = [slide["icon"] for slide in INTRO_SLIDES]
    assert len(icons) == len(set(icons))  # Все иконки уникальны
