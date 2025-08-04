"""
Тесты для документов и новостей
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram.types import Message, CallbackQuery, User as TelegramUser
from aiogram.filters import Command

from app.routes.docs import (
    show_docs,
    send_doc_link,
    back_to_docs_list,
    show_news,
    admin_announce,
    get_recipients
)
from app.repositories.user_repo import get_user
from app.i18n import t
from app.roles import UserRole


class TestDocsAndNews:
    """Тесты для документов и новостей"""
    
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
        callback.message.answer = AsyncMock()
        return callback
    
    @pytest.mark.asyncio
    async def test_show_docs_success(self, mock_message, monkeypatch):
        """Тест успешного показа документов"""
        # Мокаем get_user
        async def mock_get_user(tg_id):
            user = MagicMock()
            user.role = "teacher"
            return user
        monkeypatch.setattr("app.repositories.user_repo.get_user", mock_get_user)
        
        # Мокаем t функцию
        def mock_t(key):
            key_map = {
                "docs.list_header": "📄 Список доступных документов:",
                "docs.item_standard": "• Порядок оказания психолого‑педагогической помощи",
                "docs.item_pay": "• Методика оплаты труда педагогических работников",
                "docs.item_help": "• Официальные контакты служб помощи",
                "docs.reply_footer": "Выберите документ для получения ссылки или краткой информации."
            }
            return key_map.get(key, key)
        monkeypatch.setattr("app.i18n.t", mock_t)
        
        await show_docs(mock_message)
        
        # Проверяем, что ответ был отправлен
        mock_message.answer.assert_called_once()
        call_args = mock_message.answer.call_args
        assert "📄 Список доступных документов:" in call_args[0][0]
        assert call_args[1]["reply_markup"] is not None
    
    @pytest.mark.asyncio
    async def test_show_docs_no_user(self, mock_message, monkeypatch):
        """Тест показа документов без авторизации"""
        # Мокаем get_user
        async def mock_get_user(tg_id):
            return None
        monkeypatch.setattr("app.routes.docs.get_user", mock_get_user)
        
        await show_docs(mock_message)
        
        # Проверяем, что отправлено сообщение об ошибке
        mock_message.answer.assert_called_once()
        assert "❌ Для доступа к документам необходимо войти в систему" in mock_message.answer.call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_send_doc_link_success(self, mock_callback, monkeypatch):
        """Тест успешной отправки ссылки на документ"""
        mock_callback.data = "doc_standard"
        
        await send_doc_link(mock_callback)
        
        # Проверяем, что сообщение было отредактировано
        mock_callback.message.edit_text.assert_called_once()
        call_args = mock_callback.message.edit_text.call_args
        assert "Порядок оказания психолого-педагогической помощи" in call_args[0][0]
        assert call_args[1]["parse_mode"] == "HTML"
        mock_callback.answer.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_doc_link_unknown(self, mock_callback, monkeypatch):
        """Тест отправки неизвестного документа"""
        mock_callback.data = "doc_unknown"
        
        # Мокаем t функцию
        def mock_t(key):
            if key == "docs.unknown_doc":
                return "Документ не найден. Уточните запрос."
            return key
        monkeypatch.setattr("app.routes.docs.t", mock_t)
        
        await send_doc_link(mock_callback)
        
        # Проверяем, что отправлено сообщение об ошибке
        mock_callback.message.answer.assert_called_once()
        assert "Документ не найден" in mock_callback.message.answer.call_args[0][0]
        mock_callback.answer.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_back_to_docs_list(self, mock_callback, monkeypatch):
        """Тест возврата к списку документов"""
        # Мокаем t функцию
        def mock_t(key):
            key_map = {
                "docs.list_header": "📄 Список доступных документов:",
                "docs.item_standard": "• Порядок оказания психолого‑педагогической помощи",
                "docs.item_pay": "• Методика оплаты труда педагогических работников",
                "docs.item_help": "• Официальные контакты служб помощи",
                "docs.reply_footer": "Выберите документ для получения ссылки или краткой информации."
            }
            return key_map.get(key, key)
        monkeypatch.setattr("app.routes.docs.t", mock_t)
        
        await back_to_docs_list(mock_callback)
        
        # Проверяем, что сообщение было отредактировано
        mock_callback.message.edit_text.assert_called_once()
        call_args = mock_callback.message.edit_text.call_args
        assert "📄 Список доступных документов:" in call_args[0][0]
        mock_callback.answer.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_show_news_success(self, mock_message, monkeypatch):
        """Тест успешного показа новостей"""
        # Мокаем get_user
        async def mock_get_user(tg_id):
            user = MagicMock()
            user.role = "student"
            return user
        monkeypatch.setattr("app.routes.docs.get_user", mock_get_user)
        
        # Мокаем get_news_cards
        def mock_get_news_cards(limit=5):
            return [
                {
                    "title": "Тестовая новость",
                    "date": "01.01.2024",
                    "desc": "Описание новости",
                    "url": "https://example.com"
                }
            ]
        monkeypatch.setattr("app.routes.docs.get_news_cards", mock_get_news_cards)
        
        # Мокаем t функцию
        def mock_t(key):
            key_map = {
                "news.card_header": "📰 {title}",
                "news.card_date": "Дата: {date}",
                "news.card_desc": "{desc}",
                "news.card_more": "Подробнее"
            }
            return key_map.get(key, key)
        monkeypatch.setattr("app.routes.docs.t", mock_t)
        
        await show_news(mock_message)
        
        # Проверяем, что новости были отправлены
        assert mock_message.answer.call_count >= 2  # Новость + информация о количестве
    
    @pytest.mark.asyncio
    async def test_show_news_no_user(self, mock_message, monkeypatch):
        """Тест показа новостей без авторизации"""
        # Мокаем get_user
        async def mock_get_user(tg_id):
            return None
        monkeypatch.setattr("app.routes.docs.get_user", mock_get_user)
        
        await show_news(mock_message)
        
        # Проверяем, что отправлено сообщение об ошибке
        mock_message.answer.assert_called_once()
        assert "❌ Для доступа к новостям необходимо войти в систему" in mock_message.answer.call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_show_news_empty(self, mock_message, monkeypatch):
        """Тест показа новостей когда их нет"""
        # Мокаем get_user
        async def mock_get_user(tg_id):
            user = MagicMock()
            user.role = "student"
            return user
        monkeypatch.setattr("app.routes.docs.get_user", mock_get_user)
        
        # Мокаем get_news_cards
        def mock_get_news_cards(limit=5):
            return []
        monkeypatch.setattr("app.routes.docs.get_news_cards", mock_get_news_cards)
        
        await show_news(mock_message)
        
        # Проверяем, что отправлено сообщение о недоступности
        mock_message.answer.assert_called_once()
        assert "Новости временно недоступны" in mock_message.answer.call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_admin_announce_success(self, mock_message, monkeypatch):
        """Тест успешной отправки объявления администратором"""
        mock_message.text = "/announce Важное объявление"
        
        # Мокаем get_user
        async def mock_get_user(tg_id):
            user = MagicMock()
            user.role = UserRole.ADMIN
            return user
        monkeypatch.setattr("app.routes.docs.get_user", mock_get_user)
        
        # Мокаем t функцию
        def mock_t(key):
            if key == "admin.announcement":
                return "Уважаемые коллеги!\n\n{announcement}\n\nДокумент: {url}"
            return key
        monkeypatch.setattr("app.routes.docs.t", mock_t)
        
        await admin_announce(mock_message)
        
        # Проверяем, что объявление было отправлено
        assert mock_message.answer.call_count >= 2  # Объявление + подтверждение
    
    @pytest.mark.asyncio
    async def test_admin_announce_no_permission(self, mock_message, monkeypatch):
        """Тест отправки объявления без прав"""
        mock_message.text = "/announce Важное объявление"
        
        # Мокаем get_user
        async def mock_get_user(tg_id):
            user = MagicMock()
            user.role = UserRole.STUDENT
            return user
        monkeypatch.setattr("app.routes.docs.get_user", mock_get_user)
        
        await admin_announce(mock_message)
        
        # Проверяем, что отправлено сообщение об ошибке
        mock_message.answer.assert_called_once()
        assert "❌ У вас нет прав для отправки объявлений" in mock_message.answer.call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_admin_announce_no_text(self, mock_message, monkeypatch):
        """Тест отправки объявления без текста"""
        mock_message.text = "/announce"
        
        # Мокаем get_user
        async def mock_get_user(tg_id):
            user = MagicMock()
            user.role = UserRole.ADMIN
            return user
        monkeypatch.setattr("app.routes.docs.get_user", mock_get_user)
        
        await admin_announce(mock_message)
        
        # Проверяем, что отправлено сообщение об использовании
        mock_message.answer.assert_called_once()
        assert "Использование: /announce текст_объявления" in mock_message.answer.call_args[0][0]
    
    def test_get_recipients(self):
        """Тест получения списка получателей"""
        recipients = get_recipients("all")
        
        # Проверяем, что возвращается список
        assert isinstance(recipients, list)
        assert len(recipients) > 0 