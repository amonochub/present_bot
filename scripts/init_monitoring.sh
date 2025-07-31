#!/bin/bash
set -euo pipefail

# Скрипт для инициализации системы мониторинга
# Использование: ./scripts/init_monitoring.sh

echo "🚀 Инициализация системы мониторинга"

# Функция для проверки зависимостей
check_dependencies() {
    echo "🔍 Проверка зависимостей..."
    
    # Проверяем Docker
    if ! command -v docker &> /dev/null; then
        echo "❌ Docker не установлен"
        exit 1
    fi
    
    # Проверяем Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        echo "❌ Docker Compose не установлен"
        exit 1
    fi
    
    # Проверяем curl
    if ! command -v curl &> /dev/null; then
        echo "❌ curl не установлен"
        exit 1
    fi
    
    echo "✅ Все зависимости установлены"
}

# Функция для создания директорий
create_directories() {
    echo "📁 Создание директорий..."
    
    mkdir -p backups
    mkdir -p logs
    mkdir -p nginx
    mkdir -p grafana/provisioning/dashboards
    mkdir -p grafana/provisioning/datasources
    
    echo "✅ Директории созданы"
}

# Функция для настройки переменных окружения
setup_environment() {
    echo "⚙️ Настройка переменных окружения..."
    
    # Проверяем наличие .env
    if [[ ! -f .env ]]; then
        echo "⚠️ Файл .env не найден, копируем из примера..."
        cp env.example .env
        echo "📝 Отредактируйте .env файл с вашими настройками"
    fi
    
    # Проверяем обязательные переменные
    required_vars=("TELEGRAM_TOKEN" "POSTGRES_PASSWORD")
    missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if ! grep -q "^${var}=" .env; then
            missing_vars+=("$var")
        fi
    done
    
    if [[ ${#missing_vars[@]} -gt 0 ]]; then
        echo "⚠️ Отсутствуют переменные: ${missing_vars[*]}"
        echo "📝 Добавьте их в .env файл"
    fi
    
    echo "✅ Переменные окружения настроены"
}

# Функция для запуска сервисов
start_services() {
    echo "🚀 Запуск сервисов..."
    
    # Запускаем базовые сервисы
    docker-compose up -d postgres redis
    
    # Ждем запуска базы данных
    echo "⏳ Ожидание запуска базы данных..."
    sleep 10
    
    # Проверяем подключение к базе
    if docker-compose exec -T postgres pg_isready -U schoolbot > /dev/null 2>&1; then
        echo "✅ База данных запущена"
    else
        echo "❌ База данных не запустилась"
        exit 1
    fi
    
    # Запускаем остальные сервисы
    docker-compose up -d
    
    echo "✅ Все сервисы запущены"
}

# Функция для инициализации GlitchTip
init_glitchtip() {
    echo "🔧 Инициализация GlitchTip..."
    
    # Ждем запуска GlitchTip
    echo "⏳ Ожидание запуска GlitchTip..."
    sleep 30
    
    # Применяем миграции
    if docker-compose exec -T glitchtip ./manage.py migrate > /dev/null 2>&1; then
        echo "✅ Миграции GlitchTip применены"
    else
        echo "⚠️ Ошибка применения миграций GlitchTip"
    fi
    
    # Создаем суперпользователя
    if docker-compose exec -T glitchtip ./manage.py createsuperuser --noinput > /dev/null 2>&1; then
        echo "✅ Суперпользователь GlitchTip создан"
    else
        echo "⚠️ Суперпользователь уже существует"
    fi
    
    echo "✅ GlitchTip инициализирован"
    echo "🌐 Откройте http://localhost:9000 для настройки проекта"
}

# Функция для настройки Grafana
setup_grafana() {
    echo "📊 Настройка Grafana..."
    
    # Ждем запуска Grafana
    echo "⏳ Ожидание запуска Grafana..."
    sleep 20
    
    # Проверяем доступность Grafana
    if curl -f http://localhost:3000/api/health > /dev/null 2>&1; then
        echo "✅ Grafana запущена"
    else
        echo "❌ Grafana не запустилась"
        return 1
    fi
    
    # Создаем datasource для Prometheus
    cat > grafana/provisioning/datasources/prometheus.yml << EOF
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true
EOF
    
    echo "✅ Datasource Prometheus настроен"
}

# Функция для настройки Alertmanager
setup_alertmanager() {
    echo "🔔 Настройка Alertmanager..."
    
    # Проверяем наличие переменных для Telegram
    if grep -q "TELEGRAM_BOT_TOKEN" .env && grep -q "TELEGRAM_CHAT_ID" .env; then
        echo "✅ Переменные Telegram настроены"
    else
        echo "⚠️ Переменные Telegram не настроены"
        echo "📝 Добавьте в .env:"
        echo "TELEGRAM_BOT_TOKEN=your_bot_token"
        echo "TELEGRAM_CHAT_ID=your_chat_id"
    fi
    
    # Проверяем доступность Alertmanager
    if curl -f http://localhost:9093/api/v1/status > /dev/null 2>&1; then
        echo "✅ Alertmanager запущен"
    else
        echo "❌ Alertmanager не запустился"
        return 1
    fi
}

# Функция для проверки метрик
check_metrics() {
    echo "📈 Проверка метрик..."
    
    # Проверяем Prometheus
    if curl -f http://localhost:9090/api/v1/status/targets > /dev/null 2>&1; then
        echo "✅ Prometheus работает"
    else
        echo "❌ Prometheus недоступен"
        return 1
    fi
    
    # Проверяем метрики бота
    if curl -f http://localhost:8080/metrics > /dev/null 2>&1; then
        echo "✅ Метрики бота доступны"
    else
        echo "❌ Метрики бота недоступны"
        return 1
    fi
    
    # Проверяем health check
    if curl -f http://localhost:8080/healthz > /dev/null 2>&1; then
        echo "✅ Health check работает"
    else
        echo "❌ Health check недоступен"
        return 1
    fi
}

# Функция для создания дашборда
create_dashboard() {
    echo "📊 Создание дашборда..."
    
    # Создаем базовый дашборд
    cat > grafana/provisioning/dashboards/schoolbot.json << EOF
{
  "dashboard": {
    "id": null,
    "title": "SchoolBot Dashboard",
    "tags": ["schoolbot", "telegram"],
    "timezone": "browser",
    "panels": [
      {
        "id": 1,
        "title": "Requests per Second",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(bot_requests_total[5m])",
            "legendFormat": "req/s"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0}
      },
      {
        "id": 2,
        "title": "Errors per Second",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(bot_errors_total[5m])",
            "legendFormat": "errors/s"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0}
      },
      {
        "id": 3,
        "title": "95th Percentile Latency",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(bot_latency_seconds_bucket[5m]))",
            "legendFormat": "p95"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8}
      },
      {
        "id": 4,
        "title": "Open Tickets",
        "type": "stat",
        "targets": [
          {
            "expr": "bot_tickets_open",
            "legendFormat": "tickets"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8}
      }
    ],
    "time": {"from": "now-1h", "to": "now"},
    "refresh": "10s"
  }
}
EOF
    
    # Создаем конфигурацию дашбордов
    cat > grafana/provisioning/dashboards/dashboards.yml << EOF
apiVersion: 1

providers:
  - name: 'default'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /etc/grafana/provisioning/dashboards
EOF
    
    echo "✅ Дашборд создан"
}

# Функция для финальной проверки
final_check() {
    echo "✅ Финальная проверка..."
    
    echo ""
    echo "📊 Доступные сервисы:"
    echo "- 🌐 Grafana: http://localhost:3000 (admin/admin123)"
    echo "- 📈 Prometheus: http://localhost:9090"
    echo "- 🔔 Alertmanager: http://localhost:9093"
    echo "- 🤖 Bot Health: http://localhost:8080/healthz"
    echo "- 📊 Bot Metrics: http://localhost:8080/metrics"
    echo "- 🐛 GlitchTip: http://localhost:9000"
    
    echo ""
    echo "📋 Следующие шаги:"
    echo "1. Откройте Grafana и войдите под admin/admin123"
    echo "2. Настройте GlitchTip проект в http://localhost:9000"
    echo "3. Добавьте GLITCHTIP_DSN в .env"
    echo "4. Настройте Telegram уведомления в .env"
    echo "5. Проверьте алерты в Alertmanager"
    
    echo ""
    echo "🎉 Система мониторинга инициализирована!"
}

# Основной процесс
main() {
    echo "📋 План инициализации:"
    echo "1. Проверка зависимостей"
    echo "2. Создание директорий"
    echo "3. Настройка переменных окружения"
    echo "4. Запуск сервисов"
    echo "5. Инициализация GlitchTip"
    echo "6. Настройка Grafana"
    echo "7. Настройка Alertmanager"
    echo "8. Проверка метрик"
    echo "9. Создание дашборда"
    echo "10. Финальная проверка"
    echo ""
    
    check_dependencies
    create_directories
    setup_environment
    start_services
    init_glitchtip
    setup_grafana
    setup_alertmanager
    check_metrics
    create_dashboard
    final_check
}

# Запуск основного процесса
main "$@" 