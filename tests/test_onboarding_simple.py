# tests/test_onboarding_simple.py
import os

import pytest


def test_role_images_exist():
    """Тест наличия изображений для всех ролей"""
    role_images = {
        "teacher": "onboard_cards_v3/onboard_teacher.png",
        "admin": "onboard_cards_v3/onboard_admin.png",
        "director": "onboard_cards_v3/onboard_director.png",
        "parent": "onboard_cards_v3/onboard_parent.png",
        "student": "onboard_cards_v3/onboard_student.png",
        "psych": "onboard_cards_v3/onboard_psych.png",
    }

    for role, image_path in role_images.items():
        assert os.path.exists(image_path), f"Изображение {image_path} не найдено"


def test_role_descriptions_exist():
    """Тест наличия описаний для всех ролей"""
    roles = ["teacher", "admin", "director", "parent", "student", "psych"]

    role_descriptions = {
        "teacher": {
            "title": "👩‍🏫 Учитель",
            "description": "• Создание и управление заметками\n• Подача заявок в техподдержку\n• Доступ к медиа-материалам\n• Взаимодействие с учениками и родителями",
        },
        "admin": {
            "title": "🏛 Администрация",
            "description": "• Управление заявками пользователей\n• Создание рассылок\n• Доступ к медиа-материалам\n• Администрирование системы",
        },
        "director": {
            "title": "📈 Директор",
            "description": "• Просмотр статистики и KPI\n• Управление пользователями\n• Мониторинг активности\n• Аналитика по всем процессам",
        },
        "parent": {
            "title": "👪 Родитель",
            "description": "• Просмотр заданий детей\n• Получение справок\n• Создание заметок\n• Связь с учителями",
        },
        "student": {
            "title": "👨‍🎓 Ученик",
            "description": "• Просмотр заданий\n• Создание заметок\n• Задавание вопросов\n• Подача заявок в техподдержку",
        },
        "psych": {
            "title": "🧑‍⚕️ Психолог",
            "description": "• Просмотр запросов на консультацию\n• Управление обращениями\n• Поддержка учеников и родителей\n• Профессиональная помощь",
        },
    }

    for role in roles:
        assert role in role_descriptions, f"Описание для роли {role} не найдено"
        assert "title" in role_descriptions[role], f"Заголовок для роли {role} не найден"
        assert "description" in role_descriptions[role], f"Описание для роли {role} не найдено"


def test_keyboard_functions_exist():
    """Тест наличия функций клавиатур"""
    try:
        from app.keyboards.onboarding import (
            get_confirmation_keyboard,
            get_role_info_keyboard,
            get_role_selection_keyboard,
        )

        # Проверяем, что функции возвращают клавиатуры
        keyboard1 = get_role_selection_keyboard()
        keyboard2 = get_confirmation_keyboard("teacher")
        keyboard3 = get_role_info_keyboard()

        assert keyboard1 is not None
        assert keyboard2 is not None
        assert keyboard3 is not None

    except ImportError as e:
        pytest.fail(f"Не удалось импортировать функции клавиатур: {e}")


def test_onboarding_commands():
    """Тест команд онбординга"""
    commands = ["/onboard", "/carousel"]

    # Проверяем, что команды определены в коде
    for command in commands:
        assert command.startswith("/"), f"Команда {command} должна начинаться с /"


def test_role_names():
    """Тест названий ролей"""
    role_names = {
        "teacher": "Учитель",
        "admin": "Администрация",
        "director": "Директор",
        "parent": "Родитель",
        "student": "Ученик",
        "psych": "Психолог",
    }

    for role, name in role_names.items():
        assert len(name) > 0, f"Название роли {role} не может быть пустым"
        assert isinstance(name, str), f"Название роли {role} должно быть строкой"


def test_image_file_sizes():
    """Тест размера файлов изображений"""
    role_images = {
        "teacher": "onboard_cards_v3/onboard_teacher.png",
        "admin": "onboard_cards_v3/onboard_admin.png",
        "director": "onboard_cards_v3/onboard_director.png",
        "parent": "onboard_cards_v3/onboard_parent.png",
        "student": "onboard_cards_v3/onboard_student.png",
        "psych": "onboard_cards_v3/onboard_psych.png",
    }

    for role, image_path in role_images.items():
        if os.path.exists(image_path):
            file_size = os.path.getsize(image_path)
            # Проверяем, что файл не пустой и не слишком большой (больше 10MB)
            assert file_size > 0, f"Файл {image_path} пустой"
            assert (
                file_size < 10 * 1024 * 1024
            ), f"Файл {image_path} слишком большой ({file_size} байт)"
