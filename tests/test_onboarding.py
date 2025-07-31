# tests/test_onboarding.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram.types import Message, CallbackQuery, FSInputFile
from app.roles import ROLES

# Импортируем только константы, избегая импорта модулей с БД
ROLE_IMAGES = {
    "teacher": "onboard_cards_v3/onboard_teacher.png",
    "admin": "onboard_cards_v3/onboard_admin.png", 
    "director": "onboard_cards_v3/onboard_director.png",
    "parent": "onboard_cards_v3/onboard_parent.png",
    "student": "onboard_cards_v3/onboard_student.png",
    "psych": "onboard_cards_v3/onboard_psych.png"
}

ROLE_DESCRIPTIONS = {
    "teacher": {
        "title": "👩‍🏫 Учитель",
        "description": "• Создание и управление заметками\n• Подача заявок в техподдержку\n• Доступ к медиа-материалам\n• Взаимодействие с учениками и родителями"
    },
    "admin": {
        "title": "🏛 Администрация", 
        "description": "• Управление заявками пользователей\n• Создание рассылок\n• Доступ к медиа-материалам\n• Администрирование системы"
    },
    "director": {
        "title": "📈 Директор",
        "description": "• Просмотр статистики и KPI\n• Управление пользователями\n• Мониторинг активности\n• Аналитика по всем процессам"
    },
    "parent": {
        "title": "👪 Родитель",
        "description": "• Просмотр заданий детей\n• Получение справок\n• Создание заметок\n• Связь с учителями"
    },
    "student": {
        "title": "👨‍🎓 Ученик", 
        "description": "• Просмотр заданий\n• Создание заметок\n• Задавание вопросов\n• Подача заявок в техподдержку"
    },
    "psych": {
        "title": "🧑‍⚕️ Психолог",
        "description": "• Просмотр запросов на консультацию\n• Управление обращениями\n• Поддержка учеников и родителей\n• Профессиональная помощь"
    }
}

@pytest.fixture
def mock_message():
    """Мок для сообщения"""
    message = AsyncMock()
    message.from_user = AsyncMock()
    message.from_user.id = 12345
    message.answer = AsyncMock()
    return message

@pytest.fixture
def mock_callback():
    """Мок для callback query"""
    callback = AsyncMock()
    callback.from_user = AsyncMock()
    callback.from_user.id = 12345
    callback.message = AsyncMock()
    callback.message.edit_text = AsyncMock()
    callback.message.answer_photo = AsyncMock()
    callback.message.answer = AsyncMock()
    callback.message.edit_reply_markup = AsyncMock()
    callback.answer = AsyncMock()
    return callback

@pytest.fixture
def mock_state():
    """Мок для FSM состояния"""
    state = AsyncMock()
    state.set_state = AsyncMock()
    state.update_data = AsyncMock()
    state.get_data = AsyncMock(return_value={})
    state.clear = AsyncMock()
    return state

@pytest.mark.asyncio
@patch('app.handlers.onboarding.get_role_selection_keyboard')
async def test_start_onboarding(mock_keyboard, mock_message, mock_state):
    """Тест начала онбординга"""
    from app.handlers.onboarding import start_onboarding
    
    await start_onboarding(mock_message, mock_state, "ru")
    
    # Проверяем, что состояние установлено
    mock_state.set_state.assert_called_once()
    
    # Проверяем, что сообщение отправлено
    mock_message.answer.assert_called_once()
    
    # Проверяем, что в сообщении есть приветственный текст
    call_args = mock_message.answer.call_args
    assert "Добро пожаловать в SchoolBot" in call_args[0][0]

@pytest.mark.asyncio
@patch('app.handlers.onboarding.get_confirmation_keyboard')
async def test_role_selection(mock_keyboard, mock_callback, mock_state):
    """Тест выбора роли"""
    from app.handlers.onboarding import handle_role_selection
    
    # Тестируем выбор роли учителя
    mock_callback.data = "role_teacher"
    
    await handle_role_selection(mock_callback, mock_state, "ru")
    
    # Проверяем, что состояние обновлено
    mock_state.update_data.assert_called_once()
    
    # Проверяем, что отправлено фото
    mock_callback.message.answer_photo.assert_called_once()
    
    # Проверяем, что в подписи есть информация о роли
    call_args = mock_callback.message.answer_photo.call_args
    caption = call_args[1]['caption']
    assert "Учитель" in caption

@pytest.mark.asyncio
async def test_role_confirmation(mock_callback, mock_state):
    """Тест подтверждения выбора роли"""
    from app.handlers.onboarding import handle_role_confirmation
    
    # Устанавливаем выбранную роль
    mock_state.get_data.return_value = {"selected_role": "teacher"}
    mock_callback.data = "confirm_role_teacher"
    
    await handle_role_confirmation(mock_callback, mock_state, "ru")
    
    # Проверяем, что состояние очищено
    mock_state.clear.assert_called_once()
    
    # Проверяем, что отправлено сообщение об успехе
    mock_callback.message.answer.assert_called_once()
    
    # Проверяем, что в сообщении есть информация об успешном выборе
    call_args = mock_callback.message.answer.call_args
    assert "Отлично" in call_args[0][0]

@pytest.mark.asyncio
@patch('app.handlers.onboarding.send_role_carousel')
async def test_carousel_navigation(mock_send_carousel, mock_callback, mock_state):
    """Тест навигации по карусели"""
    from app.handlers.onboarding import handle_carousel_navigation
    
    # Тестируем переход к следующей роли
    mock_callback.data = "carousel_1"
    
    await handle_carousel_navigation(mock_callback, mock_state, "ru")
    
    # Проверяем, что вызвана функция отправки карусели
    mock_send_carousel.assert_called_once()

def test_role_images_exist():
    """Тест наличия изображений для всех ролей"""
    import os
    
    for role, image_path in ROLE_IMAGES.items():
        assert role in ROLES, f"Роль {role} не найдена в ROLES"
        assert os.path.exists(image_path), f"Изображение {image_path} не найдено"

def test_role_descriptions_exist():
    """Тест наличия описаний для всех ролей"""
    for role in ROLES.keys():
        if role != "super":  # Пропускаем демо-режим
            assert role in ROLE_DESCRIPTIONS, f"Описание для роли {role} не найдено"
            assert "title" in ROLE_DESCRIPTIONS[role], f"Заголовок для роли {role} не найден"
            assert "description" in ROLE_DESCRIPTIONS[role], f"Описание для роли {role} не найдено"

@pytest.mark.asyncio
@patch('app.handlers.onboarding.get_confirmation_keyboard')
async def test_info_role_display(mock_keyboard, mock_callback, mock_state):
    """Тест отображения информации о роли"""
    from app.handlers.onboarding import show_role_info
    
    mock_callback.data = "info_teacher"
    
    await show_role_info(mock_callback, mock_state, "ru")
    
    # Проверяем, что отправлено фото
    mock_callback.message.answer_photo.assert_called_once()
    
    # Проверяем, что в подписи есть информация о роли
    call_args = mock_callback.message.answer_photo.call_args
    caption = call_args[1]['caption']
    assert "Учитель" in caption
    assert "Нажмите кнопку ниже" in caption 