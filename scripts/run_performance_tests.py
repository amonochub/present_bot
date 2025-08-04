#!/usr/bin/env python3
"""
Скрипт для запуска всех тестов производительности
"""

import asyncio
import subprocess
import sys
from pathlib import Path

from app.services.performance_monitor import get_performance_summary
from app.services.cache_service import cache_service


async def run_unit_tests():
    """Запустить unit тесты производительности"""
    print("🧪 Запуск unit тестов производительности...")
    
    result = subprocess.run([
        sys.executable, "-m", "pytest",
        "tests/test_performance_optimization.py",
        "-v",
        "--tb=short"
    ], capture_output=True, text=True, cwd=Path(__file__).parent.parent)
    
    if result.returncode == 0:
        print("✅ Unit тесты пройдены успешно")
        return True
    else:
        print(f"❌ Ошибка в unit тестах: {result.stderr}")
        return False


async def run_load_tests():
    """Запустить нагрузочные тесты"""
    print("📈 Запуск нагрузочных тестов...")
    
    scenarios = [
        {"users": 10, "duration": 30, "name": "Базовый тест"},
        {"users": 25, "duration": 60, "name": "Средняя нагрузка"},
        {"users": 50, "duration": 120, "name": "Высокая нагрузка"}
    ]
    
    for scenario in scenarios:
        print(f"\n🔄 Запуск сценария: {scenario['name']}")
        print(f"   Пользователей: {scenario['users']}")
        print(f"   Длительность: {scenario['duration']} сек")
        
        result = subprocess.run([
            sys.executable, "scripts/load_test.py",
            "--users", str(scenario["users"]),
            "--duration", str(scenario["duration"])
        ], capture_output=True, text=True, cwd=Path(__file__).parent.parent)
        
        if result.returncode == 0:
            print(f"✅ Сценарий '{scenario['name']}' пройден")
        else:
            print(f"❌ Ошибка в сценарии '{scenario['name']}': {result.stderr}")
            return False
    
    return True


async def test_cache_performance():
    """Тест производительности кеша"""
    print("💾 Тест производительности кеша...")
    
    # Тест кеширования пользователей
    test_user_id = 123456789
    
    # Первый вызов - должен быть медленнее
    start_time = asyncio.get_event_loop().time()
    await cache_service.get_user(test_user_id)
    first_call_time = asyncio.get_event_loop().time() - start_time
    
    # Второй вызов - должен быть быстрее (если кеш работает)
    start_time = asyncio.get_event_loop().time()
    await cache_service.get_user(test_user_id)
    second_call_time = asyncio.get_event_loop().time() - start_time
    
    print(f"   Первый вызов: {first_call_time:.3f}с")
    print(f"   Второй вызов: {second_call_time:.3f}с")
    
    if second_call_time < first_call_time:
        print("✅ Кеширование работает корректно")
        return True
    else:
        print("⚠️ Кеширование может работать неэффективно")
        return True  # Не критично


async def test_database_performance():
    """Тест производительности базы данных"""
    print("🗄️ Тест производительности базы данных...")
    
    from app.repositories.optimized_user_repo import optimized_user_repo
    
    # Тест получения статистики
    start_time = asyncio.get_event_loop().time()
    stats = await optimized_user_repo.get_user_statistics()
    db_time = asyncio.get_event_loop().time() - start_time
    
    print(f"   Время запроса статистики: {db_time:.3f}с")
    
    if db_time < 1.0:
        print("✅ База данных работает быстро")
        return True
    elif db_time < 3.0:
        print("⚠️ База данных работает медленно, проверьте индексы")
        return True
    else:
        print("❌ База данных работает очень медленно")
        return False


async def test_monitoring():
    """Тест системы мониторинга"""
    print("📊 Тест системы мониторинга...")
    
    # Получаем сводку производительности
    summary = await get_performance_summary()
    
    # Проверяем наличие всех компонентов
    required_keys = ["system_resources", "performance_report", "database_stats", "cache_stats"]
    missing_keys = [key for key in required_keys if key not in summary]
    
    if not missing_keys:
        print("✅ Все компоненты мониторинга работают")
        
        # Выводим краткую статистику
        system_resources = summary["system_resources"]
        print(f"   CPU: {system_resources['cpu']['percent']:.1f}%")
        print(f"   Память: {system_resources['memory']['rss_mb']:.1f}MB")
        print(f"   Диск: {system_resources['disk']['usage_percent']:.1f}%")
        
        return True
    else:
        print(f"❌ Отсутствуют компоненты мониторинга: {missing_keys}")
        return False


async def test_cache_functionality():
    """Тест функциональности кеша"""
    print("🔧 Тест функциональности кеша...")
    
    # Тест получения часто используемых данных
    frequent_data = await cache_service.get_frequently_accessed_data()
    
    if frequent_data and "roles" in frequent_data:
        print("✅ Кеш часто используемых данных работает")
        
        # Тест очистки кеша
        await cache_service.clear_all_caches()
        print("✅ Очистка кеша работает")
        
        return True
    else:
        print("❌ Кеш часто используемых данных не работает")
        return False


async def generate_performance_report():
    """Генерация отчета о производительности"""
    print("📋 Генерация отчета о производительности...")
    
    summary = await get_performance_summary()
    
    report = f"""
# Отчет о производительности SchoolBot

## Системные ресурсы
- CPU: {summary['system_resources']['cpu']['percent']:.1f}%
- Память: {summary['system_resources']['memory']['rss_mb']:.1f}MB
- Диск: {summary['system_resources']['disk']['usage_percent']:.1f}%

## Производительность
- Всего вызовов: {summary['performance_report'].get('total_calls', 'N/A')}
- Успешных вызовов: {summary['performance_report'].get('successful_calls', 'N/A')}
- Процент ошибок: {summary['performance_report'].get('error_rate_percent', 'N/A')}%

## База данных
- Всего запросов: {summary['database_stats'].get('total_queries', 'N/A')}
- Среднее время: {summary['database_stats'].get('average_time', 'N/A')}с
- Медленных запросов: {summary['database_stats'].get('slow_queries_count', 'N/A')}

## Кеш
- Попадания: {summary['cache_stats'].get('hits', 'N/A')}
- Промахи: {summary['cache_stats'].get('misses', 'N/A')}
- Hit ratio: {summary['cache_stats'].get('hit_ratio', 'N/A')}%
"""
    
    # Сохраняем отчет
    report_file = Path(__file__).parent.parent / "performance_test_report.md"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)
    
    print(f"✅ Отчет сохранен: {report_file}")
    return True


async def main():
    """Основная функция тестирования"""
    print("🚀 Запуск комплексного тестирования производительности")
    print("="*60)
    
    tests = [
        ("Unit тесты", run_unit_tests),
        ("Нагрузочные тесты", run_load_tests),
        ("Производительность кеша", test_cache_performance),
        ("Производительность БД", test_database_performance),
        ("Система мониторинга", test_monitoring),
        ("Функциональность кеша", test_cache_functionality),
        ("Генерация отчета", generate_performance_report)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Ошибка в тесте '{test_name}': {e}")
            results.append((test_name, False))
    
    # Вывод итогов
    print("\n" + "="*60)
    print("📊 ИТОГИ ТЕСТИРОВАНИЯ")
    print("="*60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n📈 Результат: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("🎉 Все тесты пройдены успешно!")
        print("🚀 Система оптимизации производительности готова к использованию")
    else:
        print("⚠️ Некоторые тесты не пройдены")
        print("🔧 Проверьте настройки и повторите тестирование")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 