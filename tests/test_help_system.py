"""
Тесты для системы справки
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from aiogram.types import Message, CallbackQuery, User as TelegramUser
from aiogram.filters import Command

from app.routes.help import (
    help_command,
    handle_help_callback,
    help_button,
    get_role_help,
    get_role_help_keyboard,
    get_detailed_help,
    get_faq_text
)
from app.roles import UserRole
from app.db.user import User


class TestHelpSystem:
    """Тесты для системы справки"""
    
    @pytest.fixture
    def mock_message(self):
        """Мок сообщения"""
        message = MagicMock(spec=Message)
        message.from_user = MagicMock(spec=TelegramUser)
        message.from_user.id = 123456
        message.answer = AsyncMock()
        return message
    
    @pytest.fixture
    def mock_callback(self):
        """Мок callback"""
        callback = MagicMock(spec=CallbackQuery)
        callback.from_user = MagicMock(spec=TelegramUser)
        callback.from_user.id = 123456
        callback.answer = AsyncMock()
        callback.message = MagicMock()
        callback.message.edit_text = AsyncMock()
        return callback
    
    @pytest.mark.asyncio
    async def test_help_command_unauthorized(self, mock_message, monkeypatch):
        """Тест команды /help для неавторизованного пользователя"""
        # Мокаем get_user
        async def mock_get_user(tg_id):
            return None
        monkeypatch.setattr("app.routes.help.get_user", mock_get_user)
        
        # Мокаем t функцию
        def mock_t(key):
            if key == "help.help_unauthorized":
                return "❓ **Справка по SchoolBot**\n\n🎓 SchoolBot - это образовательная платформа..."
            elif key == "help.help_start_button":
                return "🚀 Начать"
            return key
        monkeypatch.setattr("app.routes.help.t", mock_t)
        
        await help_command(mock_message)
        
        # Проверяем, что ответ был отправлен
        mock_message.answer.assert_called_once()
        call_args = mock_message.answer.call_args
        assert "❓ **Справка по SchoolBot**" in call_args[0][0]
        assert call_args[1]["parse_mode"] == "HTML"
    
    @pytest.mark.asyncio
    async def test_help_command_authorized(self, mock_message, monkeypatch):
        """Тест команды /help для авторизованного пользователя"""
        # Мокаем get_user
        async def mock_get_user(tg_id):
            user = MagicMock()
            user.role = UserRole.STUDENT
            return user
        monkeypatch.setattr("app.routes.help.get_user", mock_get_user)
        
        await help_command(mock_message)
        
        # Проверяем, что ответ был отправлен
        mock_message.answer.assert_called_once()
        call_args = mock_message.answer.call_args
        assert "👨‍🎓 **Справка для ученика**" in call_args[0][0]
        assert call_args[1]["parse_mode"] == "HTML"
    
    @pytest.mark.asyncio
    async def test_help_callback_start(self, mock_callback, monkeypatch):
        """Тест callback для кнопки 'Начать'"""
        mock_callback.data = "help:start"
        
        # Мокаем t функцию
        def mock_t(key):
            if key == "help.help_start_message":
                return "🚀 Для начала работы нажмите /start"
            return key
        monkeypatch.setattr("app.routes.help.t", mock_t)
        
        await handle_help_callback(mock_callback)
        
        # Проверяем, что сообщение было отредактировано
        mock_callback.message.edit_text.assert_called_once()
        assert "🚀 Для начала работы нажмите /start" in mock_callback.message.edit_text.call_args[0][0]
        mock_callback.answer.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_help_callback_back(self, mock_callback, monkeypatch):
        """Тест callback для кнопки 'Назад'"""
        mock_callback.data = "help:back"
        
        # Мокаем get_user
        async def mock_get_user(tg_id):
            user = MagicMock()
            user.role = UserRole.TEACHER
            return user
        monkeypatch.setattr("app.routes.help.get_user", mock_get_user)
        
        await handle_help_callback(mock_callback)
        
        # Проверяем, что сообщение было отредактировано
        mock_callback.message.edit_text.assert_called_once()
        assert "👩‍🏫 **Справка для учителя**" in mock_callback.message.edit_text.call_args[0][0]
        mock_callback.answer.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_help_callback_detail(self, mock_callback, monkeypatch):
        """Тест callback для детальной справки"""
        mock_callback.data = "help:student:tasks"
        
        await handle_help_callback(mock_callback)
        
        # Проверяем, что сообщение было отредактировано
        mock_callback.message.edit_text.assert_called_once()
        assert "📋 **Задания для ученика**" in mock_callback.message.edit_text.call_args[0][0]
        mock_callback.answer.assert_called_once()
    
    def test_get_role_help(self):
        """Тест получения справки для роли"""
        # Тест для ученика
        student_help = get_role_help(UserRole.STUDENT)
        assert "👨‍🎓 **Справка для ученика**" in student_help
        assert "📋 Просмотр заданий от учителей" in student_help
        
        # Тест для учителя
        teacher_help = get_role_help(UserRole.TEACHER)
        assert "👩‍🏫 **Справка для учителя**" in teacher_help
        assert "📝 Создание заметок о учениках" in teacher_help
        
        # Тест для неизвестной роли
        unknown_help = get_role_help("unknown")
        assert "❓ **Общая справка**" in unknown_help
    
    def test_get_role_help_keyboard(self, monkeypatch):
        """Тест получения клавиатуры для роли"""
        # Мокаем t функцию
        def mock_t(key):
            key_map = {
                "help.help_student_tasks": "📋 Задания",
                "help.help_student_notes": "📝 Заметки",
                "help.help_student_ask": "❓ Вопросы",
                "help.help_main_menu_button": "🏠 Главное меню"
            }
            return key_map.get(key, key)
        monkeypatch.setattr("app.routes.help.t", mock_t)
        
        keyboard = get_role_help_keyboard(UserRole.STUDENT)
        
        # Проверяем структуру клавиатуры
        assert len(keyboard.inline_keyboard) == 4  # 3 кнопки + главное меню
        assert keyboard.inline_keyboard[0][0].text == "📋 Задания"
        assert keyboard.inline_keyboard[1][0].text == "📝 Заметки"
        assert keyboard.inline_keyboard[2][0].text == "❓ Вопросы"
        assert keyboard.inline_keyboard[3][0].text == "🏠 Главное меню"
    
    def test_get_detailed_help(self):
        """Тест получения детальной справки"""
        # Тест для заданий ученика
        tasks_help = get_detailed_help("student", "tasks")
        assert "📋 **Задания для ученика**" in tasks_help
        assert "Как просматривать задания:" in tasks_help
        
        # Тест для заметок учителя
        notes_help = get_detailed_help("teacher", "notes")
        assert "📝 **Заметки о учениках**" in notes_help
        assert "Как создать заметку:" in notes_help
        
        # Тест для неизвестного раздела
        unknown_help = get_detailed_help("unknown", "unknown")
        assert "📖 Детальная справка по разделу unknown" in unknown_help
    
    def test_get_faq_text(self, monkeypatch):
        """Тест получения FAQ текста"""
        # Мокаем t функцию
        def mock_t(key):
            key_map = {
                "help.help_faq_title": "❓ **Часто задаваемые вопросы**",
                "help.help_faq_role_change": "**Q: Как изменить роль?**\nA: Обратитесь к администратору системы.",
                "help.help_faq_password": "**Q: Забыл пароль?**\nA: Используйте команду /start для повторной авторизации.",
                "help.help_faq_notifications": "**Q: Не получаю уведомления?**\nA: Проверьте настройки уведомлений в главном меню.",
                "help.help_faq_support": "**Q: Как связаться с поддержкой?**\nA: Используйте команду /feedback для обратной связи."
            }
            return key_map.get(key, key)
        monkeypatch.setattr("app.routes.help.t", mock_t)
        
        faq_text = get_faq_text("ru")
        
        assert "❓ **Часто задаваемые вопросы**" in faq_text
        assert "**Q: Как изменить роль?**" in faq_text
        assert "**Q: Забыл пароль?**" in faq_text
        assert "**Q: Не получаю уведомления?**" in faq_text
        assert "**Q: Как связаться с поддержкой?**" in faq_text
    
    @pytest.mark.asyncio
    async def test_help_button_success(self, mock_callback, monkeypatch):
        """Тест успешного нажатия кнопки справки"""
        # Мокаем get_user_role
        async def mock_get_user_role(tg_id):
            return UserRole.STUDENT
        monkeypatch.setattr("app.routes.help.get_user_role", mock_get_user_role)
        
        # Мокаем t функцию
        def mock_t(key):
            if key == "help.help_help_loaded":
                return "Справка загружена"
            return key
        monkeypatch.setattr("app.routes.help.t", mock_t)
        
        await help_button(mock_callback, "ru")
        
        # Проверяем, что сообщение было отредактировано
        mock_callback.message.edit_text.assert_called_once()
        assert "👨‍🎓 **Справка для ученика**" in mock_callback.message.edit_text.call_args[0][0]
        mock_callback.answer.assert_called_once_with("Справка загружена")
    
    @pytest.mark.asyncio
    async def test_help_button_user_not_found(self, mock_callback, monkeypatch):
        """Тест нажатия кнопки справки с ошибкой пользователя"""
        mock_callback.from_user = None
        
        # Мокаем t функцию
        def mock_t(key):
            if key == "help.help_user_not_found":
                return "Ошибка: пользователь не найден."
            return key
        monkeypatch.setattr("app.routes.help.t", mock_t)
        
        await help_button(mock_callback, "ru")
        
        # Проверяем, что была показана ошибка
        mock_callback.answer.assert_called_once_with("Ошибка: пользователь не найден.", show_alert=True)
    
    @pytest.mark.asyncio
    async def test_help_button_no_role(self, mock_callback, monkeypatch):
        """Тест нажатия кнопки справки без роли"""
        # Мокаем get_user_role
        async def mock_get_user_role(tg_id):
            return None
        monkeypatch.setattr("app.routes.help.get_user_role", mock_get_user_role)
        
        # Мокаем t функцию
        def mock_t(key):
            if key == "help.help_please_login":
                return "Пожалуйста, сначала войдите в систему."
            return key
        monkeypatch.setattr("app.routes.help.t", mock_t)
        
        await help_button(mock_callback, "ru")
        
        # Проверяем, что была показана ошибка
        mock_callback.answer.assert_called_once_with("Пожалуйста, сначала войдите в систему.", show_alert=True) 