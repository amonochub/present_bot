"""
Middleware для сбора метрик Prometheus
"""

import time
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from prometheus_client import Counter, Gauge, Histogram

# Метрики
REQUESTS_TOTAL = Counter("bot_requests_total", "Total number of requests")
ERRORS_TOTAL = Counter("bot_errors_total", "Total number of errors")
LATENCY_SECONDS = Histogram("bot_latency_seconds", "Request latency in seconds")
TICKETS_OPEN = Gauge("bot_tickets_open", "Number of open tickets")

# KPI метрики для поручений директора
TASKS_TOTAL = Gauge("kpi_tasks_total", "Всего поручений директора")
TASKS_COMPLETED = Gauge("kpi_tasks_done", "Выполнено поручений")
TASKS_OVERDUE = Gauge("kpi_tasks_overdue", "Просрочено поручений")


class MetricsMiddleware(BaseMiddleware):
    """Middleware для сбора метрик"""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        start_time = time.time()

        try:
            # Увеличиваем счетчик запросов
            REQUESTS_TOTAL.inc()

            # Выполняем обработчик
            result = await handler(event, data)

            # Записываем время выполнения
            LATENCY_SECONDS.observe(time.time() - start_time)

            return result

        except Exception:
            # Увеличиваем счетчик ошибок
            ERRORS_TOTAL.inc()
            raise


def increment_tickets():
    """Увеличить счетчик открытых заявок"""
    TICKETS_OPEN.inc()


def decrement_tickets():
    """Уменьшить счетчик открытых заявок"""
    TICKETS_OPEN.dec()


def set_tickets_count(count: int):
    """Установить точное количество открытых заявок"""
    TICKETS_OPEN.set(count)
