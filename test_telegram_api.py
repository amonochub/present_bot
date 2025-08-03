#!/usr/bin/env python3
import asyncio

from aiogram import Bot

from app.config import settings


async def test_telegram_api():
    """Тестируем подключение к Telegram API"""
    try:
        bot = Bot(settings.TELEGRAM_TOKEN)
        me = await bot.get_me()
        print("✅ Telegram API подключен")
        print(f"📝 Имя бота: {me.first_name}")
        print(f"🆔 ID бота: {me.id}")
        print(f"👤 Username: @{me.username}")
        await bot.session.close()
        return True
    except Exception as e:
        print(f"❌ Ошибка Telegram API: {e}")
        return False


if __name__ == "__main__":
    result = asyncio.run(test_telegram_api())
    if result:
        print("🎉 Telegram API работает корректно!")
    else:
        print("💥 Проблема с Telegram API")
