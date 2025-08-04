"""
Тесты для роутера документов и новостей с исправлениями согласно Context7
"""

import pytest
from unittest.mock import MagicMock, AsyncMock
from aiogram.types import Message, CallbackQuery, User, Chat
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from app.routes.docs import (
    show_docs, send_doc_link, back_to_docs_list, 
    show_news, admin_announce, get_localized_text
)


@pytest.fixture
def mock_message():
    """Фикстура для мокирования Message"""
    message = MagicMock(spec=Message)
    message.from_user = MagicMock(spec=User)
    message.from_user.id = 123456
    message.text = "/docs"
    message.answer = AsyncMock()
    return message


@pytest.fixture
def mock_callback():
    """Фикстура для мокирования CallbackQuery"""
    callback = MagicMock(spec=CallbackQuery)
    callback.from_user = MagicMock(spec=User)
    callback.from_user.id = 123456
    callback.data = "doc_standard"
    callback.message = MagicMock()
    callback.message.edit_text = AsyncMock()
    callback.message.answer = AsyncMock()
    callback.answer = AsyncMock()
    return callback


@pytest.fixture
def mock_user():
    """Фикстура для мокирования пользователя"""
    user = MagicMock()
    user.id = 123456
    user.role = "student"
    return user


@pytest.fixture
def mock_admin_user():
    """Фикстура для мокирования админа"""
    user = MagicMock()
    user.id = 123456
    user.role = "admin"
    return user


def test_get_localized_text():
    """Тест функции get_localized_text"""
    # Мокируем функцию t
    with pytest.MonkeyPatch().context() as m:
        m.setattr("app.i18n.t", lambda key: f"LOCALIZED_{key}")
        
        # Тест без параметров
        result = get_localized_text("test.key")
        assert result == "LOCALIZED_test.key"
        
        # Тест с параметрами
        result = get_localized_text("test.key", param="value")
        assert result == "LOCALIZED_test.key"


@pytest.mark.asyncio
async def test_show_docs_success(mock_message, mock_user, monkeypatch):
    """Тест успешного показа документов"""
    # Мокируем зависимости
    monkeypatch.setattr("app.repositories.user_repo.get_user", AsyncMock(return_value=mock_user))
    monkeypatch.setattr("app.i18n.t", lambda key: f"LOCALIZED_{key}")
    
    await show_docs(mock_message)
    
    # Проверяем, что сообщение было отправлено
    mock_message.answer.assert_called_once()
    
    # Проверяем, что в сообщении есть локализованный текст
    call_args = mock_message.answer.call_args
    assert "LOCALIZED_docs.list_header" in call_args[0][0]
    assert "LOCALIZED_docs.item_standard" in call_args[0][0]


@pytest.mark.asyncio
async def test_show_docs_no_user(mock_message, monkeypatch):
    """Тест показа документов без пользователя"""
    # Мокируем get_user для возврата None
    monkeypatch.setattr("app.repositories.user_repo.get_user", AsyncMock(return_value=None))
    
    await show_docs(mock_message)
    
    # Проверяем, что отправлено сообщение об ошибке
    mock_message.answer.assert_called_once_with("❌ Для доступа к документам необходимо войти в систему")


@pytest.mark.asyncio
async def test_send_doc_link_success(mock_callback, monkeypatch):
    """Тест успешной отправки ссылки на документ"""
    # Мокируем локализацию
    monkeypatch.setattr("app.i18n.t", lambda key: f"LOCALIZED_{key}")
    
    await send_doc_link(mock_callback)
    
    # Проверяем, что сообщение было отредактировано
    mock_callback.message.edit_text.assert_called_once()
    
    # Проверяем, что callback был отвечен
    mock_callback.answer.assert_called_once()


@pytest.mark.asyncio
async def test_send_doc_link_unknown(mock_callback, monkeypatch):
    """Тест отправки неизвестного документа"""
    mock_callback.data = "doc_unknown"
    
    # Мокируем локализацию
    monkeypatch.setattr("app.i18n.t", lambda key: f"LOCALIZED_{key}")
    
    await send_doc_link(mock_callback)
    
    # Проверяем, что отправлено сообщение об ошибке
    mock_callback.message.answer.assert_called_once_with("LOCALIZED_docs.unknown_doc")
    mock_callback.answer.assert_called_once()


@pytest.mark.asyncio
async def test_back_to_docs_list(mock_callback, monkeypatch):
    """Тест возврата к списку документов"""
    # Мокируем локализацию
    monkeypatch.setattr("app.i18n.t", lambda key: f"LOCALIZED_{key}")
    
    await back_to_docs_list(mock_callback)
    
    # Проверяем, что сообщение было отредактировано
    mock_callback.message.edit_text.assert_called_once()
    
    # Проверяем, что в сообщении есть локализованный текст
    call_args = mock_callback.message.edit_text.call_args
    assert "LOCALIZED_docs.list_header" in call_args[0][0]
    
    mock_callback.answer.assert_called_once()


@pytest.mark.asyncio
async def test_show_news_success(mock_message, mock_user, monkeypatch):
    """Тест успешного показа новостей"""
    # Мокируем зависимости
    monkeypatch.setattr("app.repositories.user_repo.get_user", AsyncMock(return_value=mock_user))
    monkeypatch.setattr("app.i18n.t", lambda key, **kwargs: f"LOCALIZED_{key}")
    
    # Мокируем новости
    mock_news = [
        {"title": "Test News 1", "date": "01.01.2024", "desc": "Description 1", "url": "http://test1.com"},
        {"title": "Test News 2", "date": "02.01.2024", "desc": "Description 2", "url": "http://test2.com"}
    ]
    monkeypatch.setattr("app.services.news_parser.get_news_cards", lambda limit: mock_news)
    
    await show_news(mock_message)
    
    # Проверяем, что отправлено несколько сообщений (по одному на новость + итоговое)
    assert mock_message.answer.call_count == 3  # 2 новости + итоговое сообщение


@pytest.mark.asyncio
async def test_show_news_no_user(mock_message, monkeypatch):
    """Тест показа новостей без пользователя"""
    # Мокируем get_user для возврата None
    monkeypatch.setattr("app.repositories.user_repo.get_user", AsyncMock(return_value=None))
    
    await show_news(mock_message)
    
    # Проверяем, что отправлено сообщение об ошибке
    mock_message.answer.assert_called_once_with("❌ Для доступа к новостям необходимо войти в систему")


@pytest.mark.asyncio
async def test_show_news_empty(mock_message, mock_user, monkeypatch):
    """Тест показа новостей при пустом результате"""
    # Мокируем зависимости
    monkeypatch.setattr("app.repositories.user_repo.get_user", AsyncMock(return_value=mock_user))
    monkeypatch.setattr("app.services.news_parser.get_news_cards", lambda limit: [])
    
    await show_news(mock_message)
    
    # Проверяем, что отправлено сообщение о недоступности
    mock_message.answer.assert_called_once_with("📰 Новости временно недоступны. Попробуйте позже.")


@pytest.mark.asyncio
async def test_admin_announce_success(mock_message, mock_admin_user, monkeypatch):
    """Тест успешной отправки объявления админом"""
    # Мокируем зависимости
    monkeypatch.setattr("app.repositories.user_repo.get_user", AsyncMock(return_value=mock_admin_user))
    monkeypatch.setattr("app.i18n.t", lambda key, **kwargs: f"LOCALIZED_{key}")
    
    mock_message.text = "/announce Тестовое объявление"
    
    await admin_announce(mock_message)
    
    # Проверяем, что отправлено 2 сообщения (объявление + подтверждение)
    assert mock_message.answer.call_count == 2


@pytest.mark.asyncio
async def test_admin_announce_no_permission(mock_message, mock_user, monkeypatch):
    """Тест отправки объявления без прав"""
    # Мокируем обычного пользователя
    monkeypatch.setattr("app.repositories.user_repo.get_user", AsyncMock(return_value=mock_user))
    
    mock_message.text = "/announce Тестовое объявление"
    
    await admin_announce(mock_message)
    
    # Проверяем, что отправлено сообщение об ошибке прав
    mock_message.answer.assert_called_once_with("❌ У вас нет прав для отправки объявлений")


@pytest.mark.asyncio
async def test_admin_announce_no_text(mock_message, mock_admin_user, monkeypatch):
    """Тест отправки объявления без текста"""
    # Мокируем зависимости
    monkeypatch.setattr("app.repositories.user_repo.get_user", AsyncMock(return_value=mock_admin_user))
    
    mock_message.text = "/announce"
    
    await admin_announce(mock_message)
    
    # Проверяем, что отправлено сообщение об использовании
    mock_message.answer.assert_called_once_with("Использование: /announce текст_объявления")


@pytest.mark.asyncio
async def test_admin_announce_empty_text(mock_message, mock_admin_user, monkeypatch):
    """Тест отправки объявления с пустым текстом"""
    # Мокируем зависимости
    monkeypatch.setattr("app.repositories.user_repo.get_user", AsyncMock(return_value=mock_admin_user))
    
    mock_message.text = "/announce   "
    
    await admin_announce(mock_message)
    
    # Проверяем, что отправлено сообщение об использовании
    mock_message.answer.assert_called_once_with("Использование: /announce текст_объявления")


@pytest.mark.asyncio
async def test_admin_announce_none_text(mock_message, mock_admin_user, monkeypatch):
    """Тест отправки объявления с None текстом"""
    # Мокируем зависимости
    monkeypatch.setattr("app.repositories.user_repo.get_user", AsyncMock(return_value=mock_admin_user))
    
    mock_message.text = None
    
    await admin_announce(mock_message)
    
    # Проверяем, что отправлено сообщение об использовании
    mock_message.answer.assert_called_once_with("Использование: /announce текст_объявления") 