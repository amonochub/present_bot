#!/bin/bash

# Скрипт для инициализации системы мониторинга
echo "🚀 Инициализация системы мониторинга..."

# Проверяем, что контейнеры запущены
echo "📋 Проверка контейнеров..."
docker-compose ps

# Проверяем доступность сервисов
echo "🔍 Проверка доступности сервисов..."

# Prometheus
echo "📊 Prometheus: http://localhost:9090"
curl -s http://localhost:9090/-/healthy > /dev/null && echo "✅ Prometheus доступен" || echo "❌ Prometheus недоступен"

# Grafana
echo "📈 Grafana: http://localhost:3000"
curl -s http://localhost:3000/api/health > /dev/null && echo "✅ Grafana доступен" || echo "❌ Grafana недоступен"

# Alertmanager
echo "🔔 Alertmanager: http://localhost:9093"
curl -s http://localhost:9093/-/healthy > /dev/null && echo "✅ Alertmanager доступен" || echo "❌ Alertmanager недоступен"

# Bot metrics
echo "🤖 Bot metrics: http://localhost:8080/metrics"
curl -s http://localhost:8080/metrics > /dev/null && echo "✅ Bot metrics доступны" || echo "❌ Bot metrics недоступны"

echo ""
echo "✅ Инициализация завершена!"
echo ""
echo "🌐 Доступные сервисы:"
echo "  📊 Prometheus: http://localhost:9090"
echo "  📈 Grafana: http://localhost:3000 (admin/admin123)"
echo "  🔔 Alertmanager: http://localhost:9093"
echo "  🤖 Bot Health: http://localhost:8080/healthz"
echo "  📊 Bot Metrics: http://localhost:8080/metrics"
echo ""
echo "📝 Настройка Telegram уведомлений:"
echo "  1. Создайте бота @BotFather"
echo "  2. Добавьте в чат/канал"
echo "  3. Получите chat_id: https://api.telegram.org/bot<TOKEN>/getUpdates"
echo "  4. Добавьте в .env:"
echo "     TELEGRAM_BOT_TOKEN=123456:ABC..."
echo "     TELEGRAM_CHAT_ID=-987654321"
echo ""
echo "🧪 Для тестирования алертов:"
echo "  - Отправьте боту /crash (вызовет HighErrorRate)"
echo "  - Создайте >10 заявок (вызовет TooManyOpenTickets)" 