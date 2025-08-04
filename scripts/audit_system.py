#!/usr/bin/env python3
"""
Скрипт для регулярного аудита системы
"""

import asyncio
import json
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any

import aiohttp
import psutil
from sqlalchemy import text

from app.config import settings
from app.db.session import AsyncSessionLocal
from app.services.performance_monitor import get_performance_summary


class SystemAuditor:
    """Аудитор системы для регулярных проверок"""
    
    def __init__(self):
        self.audit_results = {
            "timestamp": datetime.now().isoformat(),
            "checks": {},
            "recommendations": [],
            "critical_issues": []
        }
    
    async def audit_dependencies(self) -> Dict[str, Any]:
        """Аудит зависимостей проекта"""
        print("📦 Проверка зависимостей...")
        
        try:
            # Проверка устаревших пакетов
            result = subprocess.run([
                sys.executable, "-m", "pip", "list", "--outdated"
            ], capture_output=True, text=True)
            
            outdated_packages = []
            if result.stdout:
                for line in result.stdout.strip().split('\n')[2:]:  # Пропускаем заголовки
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 3:
                            outdated_packages.append({
                                "package": parts[0],
                                "current": parts[1],
                                "latest": parts[2]
                            })
            
            # Проверка безопасности
            security_result = subprocess.run([
                sys.executable, "-m", "safety", "check", "--json"
            ], capture_output=True, text=True)
            
            security_issues = []
            if security_result.stdout:
                try:
                    security_data = json.loads(security_result.stdout)
                    security_issues = security_data.get("vulnerabilities", [])
                except json.JSONDecodeError:
                    pass
            
            result = {
                "outdated_packages": outdated_packages,
                "security_issues": security_issues,
                "status": "warning" if outdated_packages or security_issues else "ok"
            }
            
            if outdated_packages:
                self.audit_results["recommendations"].append(
                    f"Обновить {len(outdated_packages)} устаревших пакетов"
                )
            
            if security_issues:
                self.audit_results["critical_issues"].append(
                    f"Найдено {len(security_issues)} уязвимостей безопасности"
                )
            
            print(f"✅ Зависимости проверены: {len(outdated_packages)} устаревших, {len(security_issues)} уязвимостей")
            return result
            
        except Exception as e:
            print(f"❌ Ошибка проверки зависимостей: {e}")
            return {"status": "error", "error": str(e)}
    
    async def audit_code_quality(self) -> Dict[str, Any]:
        """Аудит качества кода"""
        print("🔍 Проверка качества кода...")
        
        try:
            # Проверка линтера
            lint_result = subprocess.run([
                sys.executable, "-m", "ruff", "check", "app/", "--output-format=json"
            ], capture_output=True, text=True)
            
            lint_issues = []
            if lint_result.stdout:
                try:
                    lint_data = json.loads(lint_result.stdout)
                    lint_issues = lint_data
                except json.JSONDecodeError:
                    pass
            
            # Проверка типов
            type_result = subprocess.run([
                sys.executable, "-m", "mypy", "app/", "--json"
            ], capture_output=True, text=True)
            
            type_issues = []
            if type_result.stdout:
                try:
                    type_data = json.loads(type_result.stdout)
                    type_issues = type_data
                except json.JSONDecodeError:
                    pass
            
            # Проверка покрытия тестами
            coverage_result = subprocess.run([
                sys.executable, "-m", "pytest", "--cov=app", "--cov-report=json"
            ], capture_output=True, text=True)
            
            coverage_data = {}
            if coverage_result.returncode == 0:
                try:
                    coverage_data = json.loads(coverage_result.stdout)
                except json.JSONDecodeError:
                    pass
            
            result = {
                "lint_issues": len(lint_issues),
                "type_issues": len(type_issues),
                "coverage": coverage_data.get("totals", {}).get("percent", 0),
                "status": "warning" if lint_issues or type_issues else "ok"
            }
            
            if lint_issues:
                self.audit_results["recommendations"].append(
                    f"Исправить {len(lint_issues)} проблем с линтером"
                )
            
            if type_issues:
                self.audit_results["recommendations"].append(
                    f"Исправить {len(type_issues)} проблем с типами"
                )
            
            if coverage_data.get("totals", {}).get("percent", 0) < 80:
                self.audit_results["recommendations"].append(
                    "Увеличить покрытие тестами до 80%"
                )
            
            print(f"✅ Качество кода проверено: {len(lint_issues)} линтер, {len(type_issues)} типы, {result['coverage']}% покрытие")
            return result
            
        except Exception as e:
            print(f"❌ Ошибка проверки качества кода: {e}")
            return {"status": "error", "error": str(e)}
    
    async def audit_database(self) -> Dict[str, Any]:
        """Аудит базы данных"""
        print("🗄️ Проверка базы данных...")
        
        try:
            async with AsyncSessionLocal() as session:
                # Проверка подключения
                await session.execute(text("SELECT 1"))
                
                # Проверка размера БД
                size_result = await session.execute(text("""
                    SELECT pg_size_pretty(pg_database_size(current_database())) as size
                """))
                db_size = size_result.scalar()
                
                # Проверка медленных запросов
                slow_queries_result = await session.execute(text("""
                    SELECT query, mean_time, calls 
                    FROM pg_stat_statements 
                    WHERE mean_time > 1000 
                    ORDER BY mean_time DESC 
                    LIMIT 10
                """))
                slow_queries = [{"query": row[0], "mean_time": row[1], "calls": row[2]} 
                               for row in slow_queries_result.fetchall()]
                
                # Проверка индексов
                indexes_result = await session.execute(text("""
                    SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
                    FROM pg_stat_user_indexes 
                    WHERE idx_scan = 0
                """))
                unused_indexes = [{"table": row[1], "index": row[2]} 
                                for row in indexes_result.fetchall()]
                
                result = {
                    "db_size": db_size,
                    "slow_queries": len(slow_queries),
                    "unused_indexes": len(unused_indexes),
                    "status": "warning" if slow_queries or unused_indexes else "ok"
                }
                
                if slow_queries:
                    self.audit_results["recommendations"].append(
                        f"Оптимизировать {len(slow_queries)} медленных запросов"
                    )
                
                if unused_indexes:
                    self.audit_results["recommendations"].append(
                        f"Удалить {len(unused_indexes)} неиспользуемых индексов"
                    )
                
                print(f"✅ База данных проверена: размер {db_size}, {len(slow_queries)} медленных запросов")
                return result
                
        except Exception as e:
            print(f"❌ Ошибка проверки БД: {e}")
            return {"status": "error", "error": str(e)}
    
    async def audit_security(self) -> Dict[str, Any]:
        """Аудит безопасности"""
        print("🔒 Проверка безопасности...")
        
        try:
            # Проверка переменных окружения
            env_vars = {
                "TELEGRAM_TOKEN": bool(settings.TELEGRAM_TOKEN),
                "DB_PASS": len(settings.DB_PASS) >= 8,
                "GLITCHTIP_DSN": bool(settings.GLITCHTIP_DSN),
                "ENV": settings.ENV in ["prod", "staging", "dev"]
            }
            
            # Проверка файлов с секретами
            secret_files = [
                ".env",
                "secrets.json",
                "config/secrets.yml"
            ]
            
            exposed_secrets = []
            for file_path in secret_files:
                if Path(file_path).exists():
                    exposed_secrets.append(file_path)
            
            # Проверка прав доступа к файлам
            sensitive_files = [
                ".env",
                "docker-compose.yml",
                "requirements.txt"
            ]
            
            permission_issues = []
            for file_path in sensitive_files:
                if Path(file_path).exists():
                    stat = Path(file_path).stat()
                    if stat.st_mode & 0o777 != 0o600:  # Проверяем права доступа
                        permission_issues.append(file_path)
            
            result = {
                "env_vars_secure": all(env_vars.values()),
                "exposed_secrets": len(exposed_secrets),
                "permission_issues": len(permission_issues),
                "status": "warning" if exposed_secrets or permission_issues else "ok"
            }
            
            if exposed_secrets:
                self.audit_results["critical_issues"].append(
                    f"Найдено {len(exposed_secrets)} файлов с секретами"
                )
            
            if permission_issues:
                self.audit_results["recommendations"].append(
                    f"Исправить права доступа для {len(permission_issues)} файлов"
                )
            
            print(f"✅ Безопасность проверена: {len(exposed_secrets)} секретов, {len(permission_issues)} прав доступа")
            return result
            
        except Exception as e:
            print(f"❌ Ошибка проверки безопасности: {e}")
            return {"status": "error", "error": str(e)}
    
    async def audit_performance(self) -> Dict[str, Any]:
        """Аудит производительности"""
        print("⚡ Проверка производительности...")
        
        try:
            # Получаем сводку производительности
            performance_summary = await get_performance_summary()
            
            # Анализируем метрики
            system_resources = performance_summary.get("system_resources", {})
            performance_report = performance_summary.get("performance_report", {})
            
            # Проверяем критические метрики
            cpu_usage = system_resources.get("cpu", {}).get("percent", 0)
            memory_usage = system_resources.get("memory", {}).get("rss_mb", 0)
            error_rate = performance_report.get("error_rate_percent", 0)
            
            issues = []
            if cpu_usage > 80:
                issues.append(f"Высокое использование CPU: {cpu_usage}%")
            
            if memory_usage > 1000:
                issues.append(f"Высокое использование памяти: {memory_usage}MB")
            
            if error_rate > 5:
                issues.append(f"Высокий процент ошибок: {error_rate}%")
            
            result = {
                "cpu_usage": cpu_usage,
                "memory_usage": memory_usage,
                "error_rate": error_rate,
                "issues": len(issues),
                "status": "warning" if issues else "ok"
            }
            
            if issues:
                for issue in issues:
                    self.audit_results["recommendations"].append(issue)
            
            print(f"✅ Производительность проверена: CPU {cpu_usage}%, память {memory_usage}MB, ошибки {error_rate}%")
            return result
            
        except Exception as e:
            print(f"❌ Ошибка проверки производительности: {e}")
            return {"status": "error", "error": str(e)}
    
    async def audit_tests(self) -> Dict[str, Any]:
        """Аудит тестов"""
        print("🧪 Проверка тестов...")
        
        try:
            # Запуск тестов
            test_result = subprocess.run([
                sys.executable, "-m", "pytest", "--tb=short", "--json-report"
            ], capture_output=True, text=True)
            
            # Парсим результаты
            test_data = {}
            if test_result.returncode == 0:
                try:
                    # Ищем JSON отчет в выводе
                    import re
                    json_match = re.search(r'\{.*\}', test_result.stdout)
                    if json_match:
                        test_data = json.loads(json_match.group())
                except:
                    pass
            
            # Подсчитываем результаты
            total_tests = test_data.get("summary", {}).get("total", 0)
            passed_tests = test_data.get("summary", {}).get("passed", 0)
            failed_tests = test_data.get("summary", {}).get("failed", 0)
            
            result = {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
                "status": "error" if failed_tests > 0 else "ok"
            }
            
            if failed_tests > 0:
                self.audit_results["critical_issues"].append(
                    f"Провалено {failed_tests} тестов"
                )
            
            if result["success_rate"] < 95:
                self.audit_results["recommendations"].append(
                    f"Увеличить успешность тестов до 95% (сейчас {result['success_rate']:.1f}%)"
                )
            
            print(f"✅ Тесты проверены: {passed_tests}/{total_tests} пройдено ({result['success_rate']:.1f}%)")
            return result
            
        except Exception as e:
            print(f"❌ Ошибка проверки тестов: {e}")
            return {"status": "error", "error": str(e)}
    
    async def run_full_audit(self) -> Dict[str, Any]:
        """Запуск полного аудита системы"""
        print("🚀 Запуск полного аудита системы")
        print("="*60)
        
        # Выполняем все проверки
        checks = [
            ("Зависимости", self.audit_dependencies),
            ("Качество кода", self.audit_code_quality),
            ("База данных", self.audit_database),
            ("Безопасность", self.audit_security),
            ("Производительность", self.audit_performance),
            ("Тесты", self.audit_tests)
        ]
        
        for check_name, check_func in checks:
            print(f"\n{'='*20} {check_name} {'='*20}")
            try:
                result = await check_func()
                self.audit_results["checks"][check_name] = result
            except Exception as e:
                print(f"❌ Ошибка в проверке {check_name}: {e}")
                self.audit_results["checks"][check_name] = {"status": "error", "error": str(e)}
        
        # Генерируем отчет
        await self.generate_audit_report()
        
        return self.audit_results
    
    async def generate_audit_report(self):
        """Генерация отчета аудита"""
        print("\n📋 Генерация отчета аудита...")
        
        # Подсчитываем статистику
        total_checks = len(self.audit_results["checks"])
        ok_checks = sum(1 for check in self.audit_results["checks"].values() 
                       if check.get("status") == "ok")
        warning_checks = sum(1 for check in self.audit_results["checks"].values() 
                           if check.get("status") == "warning")
        error_checks = sum(1 for check in self.audit_results["checks"].values() 
                          if check.get("status") == "error")
        
        # Создаем отчет
        report = f"""
# Отчет аудита системы SchoolBot

**Дата:** {self.audit_results["timestamp"]}
**Статус:** {'✅ Хорошо' if error_checks == 0 else '⚠️ Требует внимания' if warning_checks > 0 else '❌ Критично'}

## 📊 Общая статистика
- Всего проверок: {total_checks}
- ✅ Успешно: {ok_checks}
- ⚠️ Предупреждения: {warning_checks}
- ❌ Ошибки: {error_checks}

## 🔍 Результаты проверок
"""
        
        for check_name, check_result in self.audit_results["checks"].items():
            status_emoji = {
                "ok": "✅",
                "warning": "⚠️", 
                "error": "❌"
            }.get(check_result.get("status"), "❓")
            
            report += f"\n### {check_name} {status_emoji}\n"
            report += f"- Статус: {check_result.get('status', 'unknown')}\n"
            
            if "error" in check_result:
                report += f"- Ошибка: {check_result['error']}\n"
            
            # Добавляем специфичные детали для каждой проверки
            if check_name == "Зависимости":
                outdated = len(check_result.get("outdated_packages", []))
                security = len(check_result.get("security_issues", []))
                report += f"- Устаревших пакетов: {outdated}\n"
                report += f"- Уязвимостей безопасности: {security}\n"
            
            elif check_name == "Качество кода":
                lint = check_result.get("lint_issues", 0)
                types = check_result.get("type_issues", 0)
                coverage = check_result.get("coverage", 0)
                report += f"- Проблем с линтером: {lint}\n"
                report += f"- Проблем с типами: {types}\n"
                report += f"- Покрытие тестами: {coverage}%\n"
            
            elif check_name == "База данных":
                size = check_result.get("db_size", "N/A")
                slow = check_result.get("slow_queries", 0)
                unused = check_result.get("unused_indexes", 0)
                report += f"- Размер БД: {size}\n"
                report += f"- Медленных запросов: {slow}\n"
                report += f"- Неиспользуемых индексов: {unused}\n"
            
            elif check_name == "Безопасность":
                env_secure = check_result.get("env_vars_secure", False)
                secrets = check_result.get("exposed_secrets", 0)
                permissions = check_result.get("permission_issues", 0)
                report += f"- Переменные окружения: {'✅' if env_secure else '❌'}\n"
                report += f"- Экспонированных секретов: {secrets}\n"
                report += f"- Проблем с правами доступа: {permissions}\n"
            
            elif check_name == "Производительность":
                cpu = check_result.get("cpu_usage", 0)
                memory = check_result.get("memory_usage", 0)
                errors = check_result.get("error_rate", 0)
                report += f"- CPU: {cpu}%\n"
                report += f"- Память: {memory}MB\n"
                report += f"- Ошибки: {errors}%\n"
            
            elif check_name == "Тесты":
                total = check_result.get("total_tests", 0)
                passed = check_result.get("passed_tests", 0)
                success = check_result.get("success_rate", 0)
                report += f"- Всего тестов: {total}\n"
                report += f"- Пройдено: {passed}\n"
                report += f"- Успешность: {success:.1f}%\n"
        
        # Добавляем рекомендации
        if self.audit_results["recommendations"]:
            report += "\n## 💡 Рекомендации\n"
            for i, rec in enumerate(self.audit_results["recommendations"], 1):
                report += f"{i}. {rec}\n"
        
        # Добавляем критические проблемы
        if self.audit_results["critical_issues"]:
            report += "\n## 🚨 Критические проблемы\n"
            for i, issue in enumerate(self.audit_results["critical_issues"], 1):
                report += f"{i}. {issue}\n"
        
        # Сохраняем отчет
        report_file = Path(__file__).parent.parent / f"audit_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report)
        
        print(f"✅ Отчет сохранен: {report_file}")
        
        # Выводим краткую сводку
        print(f"\n📊 СВОДКА АУДИТА")
        print(f"✅ Успешно: {ok_checks}/{total_checks}")
        print(f"⚠️ Предупреждения: {warning_checks}")
        print(f"❌ Ошибки: {error_checks}")
        
        if self.audit_results["recommendations"]:
            print(f"\n💡 Рекомендации: {len(self.audit_results['recommendations'])}")
        
        if self.audit_results["critical_issues"]:
            print(f"🚨 Критические проблемы: {len(self.audit_results['critical_issues'])}")


async def main():
    """Основная функция"""
    auditor = SystemAuditor()
    results = await auditor.run_full_audit()
    
    # Возвращаем код выхода в зависимости от результатов
    critical_issues = len(results["critical_issues"])
    if critical_issues > 0:
        print(f"\n❌ Найдено {critical_issues} критических проблем")
        sys.exit(1)
    else:
        print("\n✅ Аудит завершен успешно")
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main()) 