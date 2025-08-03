#!/usr/bin/env python3
import asyncio

from app.keyboards.main_menu import menu


async def test_callback_data():
    """Тестируем генерацию callback данных"""
    try:
        # Тестируем различные роли
        roles = ["super", "teacher", "admin", "psych", "student", "parent", "director"]

        print("🧪 Тестирование callback данных:")

        for role in roles:
            # Симулируем nonce
            test_nonce = "test123"

            # Генерируем меню
            markup = menu(role, "ru", "light", test_nonce)

            print(f"\n📋 Роль: {role}")
            print(f"🔑 Nonce: {test_nonce}")

            # Проверяем кнопки
            for row in markup.inline_keyboard:
                for button in row:
                    callback_data = button.callback_data
                    print(f"   ✅ Кнопка: {button.text}")
                    print(f"   📝 Callback: {callback_data}")

                    # Проверяем формат callback данных
                    if ":" in callback_data:
                        nonce, data = callback_data.split(":", 1)
                        print(f"   🔍 Nonce: {nonce}, Data: {data}")
                    else:
                        print("   ⚠️ Нет nonce в callback данных")

        return True

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False


if __name__ == "__main__":
    result = asyncio.run(test_callback_data())
    if result:
        print("\n🎉 Тест callback данных прошел успешно!")
    else:
        print("\n💥 Проблема с callback данными")
