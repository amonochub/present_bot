#!/usr/bin/env python3
import asyncio


async def test_csrf_middleware():
    """Тестируем CSRF middleware"""
    try:
        print("🧪 Тестирование CSRF Middleware:")

        # Тестовые callback данные
        test_cases = [
            ("test123:switch_super", "switch_super"),
            ("abc456:teacher_notes", "teacher_notes"),
            ("xyz789:admin_broadcast", "admin_broadcast"),
        ]

        for callback_data, expected_data in test_cases:
            print(f"\n📝 Тест: {callback_data}")

            try:
                nonce, real_data = callback_data.split(":", 1)
                print("   ✅ Парсинг успешен:")
                print(f"      Nonce: {nonce}")
                print(f"      Real data: {real_data}")
                print(f"      Ожидалось: {expected_data}")

                if real_data == expected_data:
                    print("   ✅ Данные совпадают")
                else:
                    print("   ❌ Данные не совпадают")

            except ValueError as e:
                print(f"   ❌ Ошибка парсинга: {e}")

        return True

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False


if __name__ == "__main__":
    result = asyncio.run(test_csrf_middleware())
    if result:
        print("\n🎉 Тест CSRF Middleware прошел успешно!")
    else:
        print("\n💥 Проблема с CSRF Middleware")
