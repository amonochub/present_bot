"""
Сервис мониторинга производительности и профилирования
"""

import asyncio
import functools
import logging
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, AsyncGenerator, Callable, Dict, List, Optional

import psutil
from prometheus_client import Counter, Gauge, Histogram

logger = logging.getLogger(__name__)

# Метрики производительности
DB_QUERY_DURATION = Histogram(
    "db_query_duration_seconds", "Database query duration"
)
CACHE_HIT_RATIO = Gauge("cache_hit_ratio", "Cache hit ratio")
MEMORY_USAGE = Gauge("memory_usage_bytes", "Memory usage in bytes")
CPU_USAGE = Gauge("cpu_usage_percent", "CPU usage percentage")
SLOW_QUERIES = Counter("slow_queries_total", "Number of slow queries (>1s)")
ERROR_RATE = Counter("error_rate_total", "Error rate per minute")


@dataclass
class PerformanceMetrics:
    """Структура для хранения метрик производительности"""

    function_name: str
    execution_time: float
    memory_before: float
    memory_after: float
    cpu_usage: float
    timestamp: datetime
    success: bool
    error_message: Optional[str] = None


class PerformanceMonitor:
    """Монитор производительности"""

    def __init__(self) -> None:
        self.metrics_history: List[PerformanceMetrics] = []
        self.slow_threshold = 1.0  # секунды
        self.max_history_size = 1000

    @asynccontextmanager
    async def monitor_function(
        self, function_name: str
    ) -> AsyncGenerator[None, None]:
        """Контекстный менеджер для мониторинга функции"""
        start_time = time.time()
        memory_before = psutil.Process().memory_info().rss
        cpu_before = psutil.cpu_percent()

        try:
            yield
            success = True
            error_message = None
        except Exception as e:
            success = False
            error_message = str(e)
            raise
        finally:
            execution_time = time.time() - start_time
            memory_after = psutil.Process().memory_info().rss
            cpu_after = psutil.cpu_percent()

            # Записываем метрики
            metrics = PerformanceMetrics(
                function_name=function_name,
                execution_time=execution_time,
                memory_before=memory_before,
                memory_after=memory_after,
                cpu_usage=(cpu_before + cpu_after) / 2,
                timestamp=datetime.now(),
                success=success,
                error_message=error_message,
            )

            self._record_metrics(metrics)

    def _record_metrics(self, metrics: PerformanceMetrics) -> None:
        """Записать метрики"""
        # Добавляем в историю
        self.metrics_history.append(metrics)

        # Ограничиваем размер истории
        if len(self.metrics_history) > self.max_history_size:
            self.metrics_history = self.metrics_history[
                -self.max_history_size :
            ]

        # Обновляем Prometheus метрики
        MEMORY_USAGE.set(metrics.memory_after)
        CPU_USAGE.set(metrics.cpu_usage)

        # Проверяем медленные запросы
        if metrics.execution_time > self.slow_threshold:
            SLOW_QUERIES.inc()
            logger.warning(
                f"Медленная функция {metrics.function_name}: "
                f"{metrics.execution_time:.2f}s"
            )

        # Проверяем ошибки
        if not metrics.success:
            ERROR_RATE.inc()
            logger.error(
                f"Ошибка в функции {metrics.function_name}: "
                f"{metrics.error_message}"
            )

    def get_performance_report(self, hours: int = 24) -> Dict[str, Any]:
        """Получить отчет о производительности за указанный период"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_metrics = [
            m for m in self.metrics_history if m.timestamp > cutoff_time
        ]

        if not recent_metrics:
            return {"error": "Нет данных за указанный период"}

        # Статистика по времени выполнения
        execution_times = [m.execution_time for m in recent_metrics]
        avg_execution_time = sum(execution_times) / len(execution_times)
        max_execution_time = max(execution_times)
        min_execution_time = min(execution_times)

        # Статистика по памяти
        memory_usage = [m.memory_after for m in recent_metrics]
        avg_memory_usage = sum(memory_usage) / len(memory_usage)
        max_memory_usage = max(memory_usage)

        # Статистика по CPU
        cpu_usage = [m.cpu_usage for m in recent_metrics]
        avg_cpu_usage = sum(cpu_usage) / len(cpu_usage)
        max_cpu_usage = max(cpu_usage)

        # Статистика по ошибкам
        total_calls = len(recent_metrics)
        successful_calls = len([m for m in recent_metrics if m.success])
        error_rate = (total_calls - successful_calls) / total_calls * 100

        # Медленные функции
        slow_functions = [
            m for m in recent_metrics if m.execution_time > self.slow_threshold
        ]

        return {
            "period_hours": hours,
            "total_calls": total_calls,
            "successful_calls": successful_calls,
            "error_rate_percent": error_rate,
            "execution_time": {
                "average": avg_execution_time,
                "maximum": max_execution_time,
                "minimum": min_execution_time,
            },
            "memory_usage": {
                "average_mb": avg_memory_usage / 1024 / 1024,
                "maximum_mb": max_memory_usage / 1024 / 1024,
            },
            "cpu_usage": {
                "average_percent": avg_cpu_usage,
                "maximum_percent": max_cpu_usage,
            },
            "slow_functions_count": len(slow_functions),
            "slow_functions": [
                {
                    "name": m.function_name,
                    "execution_time": m.execution_time,
                    "timestamp": m.timestamp.isoformat(),
                }
                for m in slow_functions
            ],
        }

    def get_system_resources(self) -> Dict[str, Any]:
        """Получить информацию о системных ресурсах"""
        process = psutil.Process()

        return {
            "memory": {
                "rss_mb": process.memory_info().rss / 1024 / 1024,
                "vms_mb": process.memory_info().vms / 1024 / 1024,
                "percent": process.memory_percent(),
            },
            "cpu": {
                "percent": process.cpu_percent(),
                "count": psutil.cpu_count(),
            },
            "disk": {
                "usage_percent": psutil.disk_usage("/").percent,
                "free_gb": psutil.disk_usage("/").free / 1024 / 1024 / 1024,
            },
            "network": {"connections": len(process.connections())},
        }


# Глобальный экземпляр монитора
performance_monitor = PerformanceMonitor()


def monitor_performance(func_name: Optional[str] = None):
    """Декоратор для мониторинга производительности функции"""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            name = func_name or f"{func.__module__}.{func.__name__}"
            async with performance_monitor.monitor_function(name):
                return await func(*args, **kwargs)

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            name = func_name or f"{func.__module__}.{func.__name__}"
            start_time = time.time()
            memory_before = psutil.Process().memory_info().rss

            try:
                result = func(*args, **kwargs)
                success = True
                error_message = None
            except Exception as e:
                success = False
                error_message = str(e)
                raise
            finally:
                execution_time = time.time() - start_time
                memory_after = psutil.Process().memory_info().rss

                metrics = PerformanceMetrics(
                    function_name=name,
                    execution_time=execution_time,
                    memory_before=memory_before,
                    memory_after=memory_after,
                    cpu_usage=psutil.cpu_percent(),
                    timestamp=datetime.now(),
                    success=success,
                    error_message=error_message,
                )

                performance_monitor._record_metrics(metrics)

            return result

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


class DatabaseProfiler:
    """Профилировщик для запросов к базе данных"""

    def __init__(self) -> None:
        self.query_times: List[float] = []
        self.slow_queries: List[Dict[str, Any]] = []

    @asynccontextmanager
    async def profile_query(
        self, query_name: str, sql: str
    ) -> AsyncGenerator[None, None]:
        """Профилировать выполнение SQL запроса"""
        start_time = time.time()

        try:
            yield
        finally:
            execution_time = time.time() - start_time
            self.query_times.append(execution_time)

            # Записываем метрики
            DB_QUERY_DURATION.observe(execution_time)

            # Проверяем медленные запросы
            if execution_time > 1.0:  # больше 1 секунды
                self.slow_queries.append(
                    {
                        "name": query_name,
                        "sql": sql,
                        "execution_time": execution_time,
                        "timestamp": datetime.now().isoformat(),
                    }
                )

                logger.warning(
                    f"Медленный запрос {query_name}: {execution_time:.2f}s"
                )

    def get_query_stats(self) -> Dict[str, Any]:
        """Получить статистику запросов"""
        if not self.query_times:
            return {"error": "Нет данных о запросах"}

        return {
            "total_queries": len(self.query_times),
            "average_time": sum(self.query_times) / len(self.query_times),
            "max_time": max(self.query_times),
            "min_time": min(self.query_times),
            "slow_queries_count": len(self.slow_queries),
            "slow_queries": self.slow_queries[
                -10:
            ],  # последние 10 медленных запросов
        }


# Глобальный экземпляр профилировщика БД
db_profiler = DatabaseProfiler()


class CacheProfiler:
    """Профилировщик для кеша"""

    def __init__(self) -> None:
        self.hits = 0
        self.misses = 0

    def record_hit(self) -> None:
        """Записать попадание в кеш"""
        self.hits += 1
        self._update_metrics()

    def record_miss(self) -> None:
        """Записать промах кеша"""
        self.misses += 1
        self._update_metrics()

    def _update_metrics(self) -> None:
        """Обновить метрики кеша"""
        total = self.hits + self.misses
        if total > 0:
            hit_ratio = self.hits / total
            CACHE_HIT_RATIO.set(hit_ratio)

    def get_stats(self) -> Dict[str, Any]:
        """Получить статистику кеша"""
        total = self.hits + self.misses
        if total == 0:
            return {"error": "Нет данных о кеше"}

        return {
            "hits": self.hits,
            "misses": self.misses,
            "total": total,
            "hit_ratio": self.hits / total,
            "miss_ratio": self.misses / total,
        }


# Глобальный экземпляр профилировщика кеша
cache_profiler = CacheProfiler()


async def get_performance_summary() -> Dict[str, Any]:
    """Получить сводку производительности"""
    return {
        "system_resources": performance_monitor.get_system_resources(),
        "performance_report": performance_monitor.get_performance_report(
            hours=1
        ),
        "database_stats": db_profiler.get_query_stats(),
        "cache_stats": cache_profiler.get_stats(),
    }
