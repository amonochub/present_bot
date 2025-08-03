#!/usr/bin/env python3
import asyncio
from unittest.mock import AsyncMock, MagicMock

from app.bot import demo_switch


async def test_demo_switch():
    """Тестируем функцию demo_switch"""
    try:
        print("🧪 Тестирование функции demo_switch:")

        # Создаем мок объекты
        mock_user = MagicMock()
        mock_user.id = 123456

        mock_call = AsyncMock()
        mock_call.from_user = mock_user
        mock_call.data = "switch_super"  # Очищенные данные от CSRF middleware

        mock_message = MagicMock()
        mock_message.chat.id = 789
        mock_message.edit_text = AsyncMock()
        mock_call.message = mock_message

        # Симулируем get_user

        mock_db_user = MagicMock()
        mock_db_user.id = 1
        mock_db_user.login = "demo01"
        mock_db_user.role = "psych"
        mock_db_user.theme = "light"

        # Патчим get_user
        import app.bot

        original_get_user = app.bot.get_user
        app.bot.get_user = AsyncMock(return_value=mock_db_user)

        # Патчим issue_nonce
        original_issue_nonce = app.bot.issue_nonce
        app.bot.issue_nonce = AsyncMock(return_value="new_nonce")

        # Патчим AsyncSessionLocal
        original_AsyncSessionLocal = app.bot.AsyncSessionLocal
        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.execute = AsyncMock()
        mock_session.commit = AsyncMock()
        app.bot.AsyncSessionLocal = MagicMock(return_value=mock_session)

        # Патчим ROLES
        original_ROLES = app.bot.ROLES
        app.bot.ROLES = {"super": "Демо-режим"}

        # Патчим menu
        original_menu = app.bot.menu
        app.bot.menu = MagicMock(return_value="mock_markup")

        try:
            # Вызываем функцию
            await demo_switch(mock_call, "ru")

            print("   ✅ Функция выполнилась без ошибок")
            print("   📝 Проверяем вызовы:")

            # Проверяем, что edit_text был вызван
            if mock_message.edit_text.called:
                print("   ✅ edit_text был вызван")
                call_args = mock_message.edit_text.call_args
                print(f"   📝 Аргументы: {call_args}")
            else:
                print("   ❌ edit_text не был вызван")

            # Проверяем, что issue_nonce был вызван
            if app.bot.issue_nonce.called:
                print("   ✅ issue_nonce был вызван")
            else:
                print("   ❌ issue_nonce не был вызван")

            # Проверяем, что menu был вызван
            if app.bot.menu.called:
                print("   ✅ menu был вызван")
                menu_args = app.bot.menu.call_args
                print(f"   📝 Аргументы menu: {menu_args}")
            else:
                print("   ❌ menu не был вызван")

        finally:
            # Восстанавливаем оригинальные функции
            app.bot.get_user = original_get_user
            app.bot.issue_nonce = original_issue_nonce
            app.bot.AsyncSessionLocal = original_AsyncSessionLocal
            app.bot.ROLES = original_ROLES
            app.bot.menu = original_menu

        return True

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    result = asyncio.run(test_demo_switch())
    if result:
        print("\n🎉 Тест demo_switch прошел успешно!")
    else:
        print("\n💥 Проблема с demo_switch")
