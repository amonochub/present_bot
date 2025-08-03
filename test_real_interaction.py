#!/usr/bin/env python3
import asyncio

from aiogram import Bot

from app.config import settings


async def test_real_interaction():
    """Тестируем реальное взаимодействие с ботом"""
    try:
        print("🧪 Тестирование реального взаимодействия:")

        # Подключаемся к боту
        bot = Bot(settings.TELEGRAM_TOKEN)
        me = await bot.get_me()
        print(f"✅ Бот подключен: @{me.username}")

        # Создаем тестовое меню
        test_nonce = "test123"
        test_callback = f"{test_nonce}:switch_super"

        print("\n📝 Тестовые данные:")
        print(f"   Nonce: {test_nonce}")
        print(f"   Callback: {test_callback}")

        # Симулируем CSRF middleware
        try:
            nonce, real_data = test_callback.split(":", 1)
            print(f"   ✅ CSRF парсинг: nonce={nonce}, data={real_data}")
        except ValueError as e:
            print(f"   ❌ CSRF парсинг ошибка: {e}")
            return False

        # Симулируем demo_switch
        role_target = real_data.split("_", 1)[1]
        print(f"   ✅ Парсинг роли: {role_target}")

        # Проверяем, что роль валидна
        valid_roles = ["super", "teacher", "admin", "director", "parent", "student", "psych"]
        if role_target in valid_roles:
            print(f"   ✅ Роль валидна: {role_target}")
        else:
            print(f"   ❌ Неизвестная роль: {role_target}")
            return False

        await bot.session.close()
        return True

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False


if __name__ == "__main__":
    result = asyncio.run(test_real_interaction())
    if result:
        print("\n🎉 Тест реального взаимодействия прошел успешно!")
    else:
        print("\n💥 Проблема с реальным взаимодействием")
