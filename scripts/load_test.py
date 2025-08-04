#!/usr/bin/env python3
"""
Скрипт для нагрузочного тестирования школьного бота
"""

import asyncio
import json
import logging
import random
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import aiohttp
import psutil
from locust import HttpUser, task, between
from prometheus_client import CollectorRegistry, Counter, Histogram, push_to_gateway

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Метрики для нагрузочного тестирования
registry = CollectorRegistry()
REQUEST_COUNT = Counter('load_test_requests_total', 'Total requests', registry=registry)
RESPONSE_TIME = Histogram('load_test_response_time_seconds', 'Response time', registry=registry)
ERROR_COUNT = Counter('load_test_errors_total', 'Total errors', registry=registry)


class BotLoadTest:
    """Класс для нагрузочного тестирования бота"""
    
    def __init__(self, bot_token: str, base_url: str = "http://localhost:8080"):
        self.bot_token = bot_token
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None
        self.results: List[Dict] = []
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def send_message(self, chat_id: int, text: str) -> Dict:
        """Отправить сообщение боту"""
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": text
        }
        
        start_time = time.time()
        try:
            async with self.session.post(url, json=data) as response:
                response_time = time.time() - start_time
                
                result = {
                    "timestamp": datetime.now().isoformat(),
                    "chat_id": chat_id,
                    "text": text,
                    "response_time": response_time,
                    "status_code": response.status,
                    "success": response.status == 200
                }
                
                if response.status != 200:
                    result["error"] = await response.text()
                
                self.results.append(result)
                REQUEST_COUNT.inc()
                RESPONSE_TIME.observe(response_time)
                
                if not result["success"]:
                    ERROR_COUNT.inc()
                
                return result
                
        except Exception as e:
            response_time = time.time() - start_time
            result = {
                "timestamp": datetime.now().isoformat(),
                "chat_id": chat_id,
                "text": text,
                "response_time": response_time,
                "status_code": 0,
                "success": False,
                "error": str(e)
            }
            
            self.results.append(result)
            REQUEST_COUNT.inc()
            ERROR_COUNT.inc()
            
            return result
    
    async def simulate_user_session(self, chat_id: int) -> List[Dict]:
        """Симулировать сессию пользователя"""
        session_results = []
        
        # Команды для тестирования
        commands = [
            "/start",
            "/help",
            "/menu",
            "Привет",
            "Как дела?",
            "/feedback"
        ]
        
        # Симуляция последовательности команд
        for command in commands:
            result = await self.send_message(chat_id, command)
            session_results.append(result)
            
            # Пауза между командами (имитация человеческого поведения)
            await asyncio.sleep(random.uniform(1, 3))
        
        return session_results
    
    async def run_concurrent_users(self, num_users: int, duration_seconds: int) -> Dict:
        """Запустить тест с одновременными пользователями"""
        logger.info(f"Запуск теста: {num_users} пользователей, {duration_seconds} секунд")
        
        start_time = time.time()
        tasks = []
        
        # Создаем задачи для каждого пользователя
        for i in range(num_users):
            chat_id = 1000000 + i  # Уникальный ID для каждого пользователя
            task = asyncio.create_task(
                self._user_session_loop(chat_id, duration_seconds)
            )
            tasks.append(task)
        
        # Ждем завершения всех задач
        await asyncio.gather(*tasks)
        
        end_time = time.time()
        actual_duration = end_time - start_time
        
        return self._generate_report(actual_duration)
    
    async def _user_session_loop(self, chat_id: int, duration_seconds: int) -> None:
        """Цикл сессии пользователя"""
        end_time = time.time() + duration_seconds
        
        while time.time() < end_time:
            # Симулируем случайные действия пользователя
            action = random.choice([
                "send_command",
                "send_text",
                "wait"
            ])
            
            if action == "send_command":
                command = random.choice(["/start", "/help", "/menu", "/feedback"])
                await self.send_message(chat_id, command)
            elif action == "send_text":
                text = random.choice([
                    "Привет", "Как дела?", "Спасибо", "Понятно"
                ])
                await self.send_message(chat_id, text)
            else:
                # Пауза
                await asyncio.sleep(random.uniform(2, 5))
    
    def _generate_report(self, duration: float) -> Dict:
        """Сгенерировать отчет о тестировании"""
        if not self.results:
            return {"error": "Нет результатов тестирования"}
        
        total_requests = len(self.results)
        successful_requests = len([r for r in self.results if r["success"]])
        failed_requests = total_requests - successful_requests
        
        response_times = [r["response_time"] for r in self.results]
        avg_response_time = sum(response_times) / len(response_times)
        max_response_time = max(response_times)
        min_response_time = min(response_times)
        
        # Группировка по статус кодам
        status_codes = {}
        for result in self.results:
            status = result["status_code"]
            status_codes[status] = status_codes.get(status, 0) + 1
        
        # Расчет RPS (запросов в секунду)
        rps = total_requests / duration
        
        return {
            "test_duration_seconds": duration,
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "failed_requests": failed_requests,
            "success_rate_percent": (successful_requests / total_requests) * 100,
            "requests_per_second": rps,
            "response_time": {
                "average_seconds": avg_response_time,
                "maximum_seconds": max_response_time,
                "minimum_seconds": min_response_time
            },
            "status_codes": status_codes,
            "system_resources": self._get_system_resources()
        }
    
    def _get_system_resources(self) -> Dict:
        """Получить информацию о системных ресурсах"""
        process = psutil.Process()
        
        return {
            "memory_mb": process.memory_info().rss / 1024 / 1024,
            "cpu_percent": process.cpu_percent(),
            "disk_usage_percent": psutil.disk_usage('/').percent
        }


class LocustBotUser(HttpUser):
    """Класс пользователя для Locust"""
    wait_time = between(1, 3)
    
    @task(3)
    def send_start_command(self):
        """Отправить команду /start"""
        self.client.post("/webhook", json={
            "update_id": random.randint(1, 1000000),
            "message": {
                "message_id": random.randint(1, 1000),
                "from": {
                    "id": random.randint(1000000, 9999999),
                    "first_name": "Test",
                    "username": "testuser"
                },
                "chat": {
                    "id": random.randint(1000000, 9999999),
                    "type": "private"
                },
                "date": int(time.time()),
                "text": "/start"
            }
        })
    
    @task(2)
    def send_help_command(self):
        """Отправить команду /help"""
        self.client.post("/webhook", json={
            "update_id": random.randint(1, 1000000),
            "message": {
                "message_id": random.randint(1, 1000),
                "from": {
                    "id": random.randint(1000000, 9999999),
                    "first_name": "Test",
                    "username": "testuser"
                },
                "chat": {
                    "id": random.randint(1000000, 9999999),
                    "type": "private"
                },
                "date": int(time.time()),
                "text": "/help"
            }
        })
    
    @task(1)
    def send_text_message(self):
        """Отправить текстовое сообщение"""
        messages = ["Привет", "Как дела?", "Спасибо", "Понятно"]
        self.client.post("/webhook", json={
            "update_id": random.randint(1, 1000000),
            "message": {
                "message_id": random.randint(1, 1000),
                "from": {
                    "id": random.randint(1000000, 9999999),
                    "first_name": "Test",
                    "username": "testuser"
                },
                "chat": {
                    "id": random.randint(1000000, 9999999),
                    "type": "private"
                },
                "date": int(time.time()),
                "text": random.choice(messages)
            }
        })


async def run_load_test_scenarios():
    """Запустить различные сценарии нагрузочного тестирования"""
    import os
    
    bot_token = os.getenv("TELEGRAM_TOKEN")
    if not bot_token:
        logger.error("TELEGRAM_TOKEN не установлен")
        return
    
    # Сценарии тестирования
    scenarios = [
        {"users": 10, "duration": 60, "name": "Низкая нагрузка"},
        {"users": 50, "duration": 120, "name": "Средняя нагрузка"},
        {"users": 100, "duration": 180, "name": "Высокая нагрузка"},
        {"users": 200, "duration": 300, "name": "Пиковая нагрузка"}
    ]
    
    async with BotLoadTest(bot_token) as load_tester:
        for scenario in scenarios:
            logger.info(f"Запуск сценария: {scenario['name']}")
            
            report = await load_tester.run_concurrent_users(
                scenario["users"], 
                scenario["duration"]
            )
            
            # Сохраняем отчет
            report_filename = f"load_test_report_{scenario['name'].lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            with open(report_filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Отчет сохранен: {report_filename}")
            
            # Отправляем метрики в Prometheus
            try:
                push_to_gateway('localhost:9091', job='load_test', registry=registry)
                logger.info("Метрики отправлены в Prometheus")
            except Exception as e:
                logger.warning(f"Не удалось отправить метрики: {e}")
            
            # Пауза между сценариями
            await asyncio.sleep(30)


def run_locust_test():
    """Запустить тест через Locust"""
    import subprocess
    import sys
    
    # Запускаем Locust
    cmd = [
        sys.executable, "-m", "locust",
        "-f", __file__,
        "--host=http://localhost:8080",
        "--users=100",
        "--spawn-rate=10",
        "--run-time=300s"
    ]
    
    subprocess.run(cmd)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Нагрузочное тестирование бота")
    parser.add_argument("--method", choices=["custom", "locust"], default="custom",
                       help="Метод тестирования")
    parser.add_argument("--users", type=int, default=50,
                       help="Количество одновременных пользователей")
    parser.add_argument("--duration", type=int, default=120,
                       help="Длительность теста в секундах")
    
    args = parser.parse_args()
    
    if args.method == "custom":
        asyncio.run(run_load_test_scenarios())
    else:
        run_locust_test() 