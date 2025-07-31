#!/bin/bash
set -euo pipefail

# Скрипт для горизонтального масштабирования бота
# Использование: ./scripts/scale.sh [instances]

INSTANCES=${1:-2}
MAX_INSTANCES=5
MIN_INSTANCES=1

echo "📈 Масштабирование бота до $INSTANCES экземпляров"

# Проверка лимитов
if [[ $INSTANCES -lt $MIN_INSTANCES ]]; then
    echo "❌ Минимальное количество экземпляров: $MIN_INSTANCES"
    exit 1
fi

if [[ $INSTANCES -gt $MAX_INSTANCES ]]; then
    echo "❌ Максимальное количество экземпляров: $MAX_INSTANCES"
    exit 1
fi

# Функция для проверки доступности ресурсов
check_resources() {
    echo "🔍 Проверка ресурсов..."

    # Проверяем доступную память
    available_memory=$(free -m | awk 'NR==2{printf "%.0f", $7}')
    required_memory=$((INSTANCES * 512))  # 512MB на экземпляр

    if [[ $available_memory -lt $required_memory ]]; then
        echo "⚠️ Внимание: Недостаточно памяти"
        echo "Доступно: ${available_memory}MB"
        echo "Требуется: ${required_memory}MB"
        read -p "Продолжить? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi

    # Проверяем CPU
    cpu_cores=$(nproc)
    if [[ $INSTANCES -gt $cpu_cores ]]; then
        echo "⚠️ Внимание: Количество экземпляров больше ядер CPU"
        echo "CPU ядер: $cpu_cores"
        echo "Экземпляров: $INSTANCES"
    fi
}

# Функция для создания конфигурации масштабирования
create_scale_config() {
    echo "⚙️ Создание конфигурации масштабирования..."

    # Создаем docker-compose.override.yml для масштабирования
    cat > docker-compose.override.yml << EOF
version: '3.9'

services:
  bot:
    deploy:
      replicas: $INSTANCES
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
        reservations:
          memory: 256M
          cpus: '0.25'
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
        window: 120s
    environment:
      - BOT_INSTANCE_ID=\${BOT_INSTANCE_ID:-0}
      - LOG_LEVEL=INFO
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/healthz"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # Load balancer для распределения нагрузки
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - bot
    restart: unless-stopped
EOF

    # Создаем конфигурацию nginx
    mkdir -p nginx
    cat > nginx/nginx.conf << EOF
events {
    worker_connections 1024;
}

http {
    upstream bot_backend {
        least_conn;
        server bot:8080 max_fails=3 fail_timeout=30s;
    }

    server {
        listen 80;

        location / {
            proxy_pass http://bot_backend;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;

            # Health check
            proxy_connect_timeout 5s;
            proxy_send_timeout 10s;
            proxy_read_timeout 10s;
        }

        location /healthz {
            proxy_pass http://bot_backend;
            access_log off;
        }

        location /metrics {
            proxy_pass http://bot_backend;
            access_log off;
        }
    }
}
EOF
}

# Функция для применения масштабирования
apply_scaling() {
    echo "🔄 Применение масштабирования..."

    # Останавливаем текущие сервисы
    docker-compose down

    # Применяем новую конфигурацию
    docker-compose up -d

    # Ждем запуска всех экземпляров
    echo "⏳ Ожидание запуска всех экземпляров..."
    sleep 30

    # Проверяем статус
    docker-compose ps
}

# Функция для проверки масштабирования
verify_scaling() {
    echo "✅ Проверка масштабирования..."

    # Проверяем количество запущенных контейнеров
    running_instances=$(docker-compose ps bot | grep -c "Up")

    if [[ $running_instances -eq $INSTANCES ]]; then
        echo "✅ Запущено $running_instances экземпляров из $INSTANCES"
    else
        echo "❌ Запущено $running_instances экземпляров, ожидалось $INSTANCES"
        return 1
    fi

    # Проверяем health check
    if curl -f http://localhost/healthz > /dev/null 2>&1; then
        echo "✅ Load balancer работает"
    else
        echo "❌ Load balancer недоступен"
        return 1
    fi

    # Проверяем метрики
    if curl -f http://localhost/metrics > /dev/null 2>&1; then
        echo "✅ Метрики доступны"
    else
        echo "❌ Метрики недоступны"
        return 1
    fi
}

# Функция для мониторинга производительности
monitor_performance() {
    echo "📊 Мониторинг производительности..."

    echo "Использование ресурсов:"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"

    echo ""
    echo "Логи последних запросов:"
    docker-compose logs --tail=10 bot
}

# Основной процесс
main() {
    echo "📋 План масштабирования:"
    echo "1. Проверка ресурсов"
    echo "2. Создание конфигурации"
    echo "3. Применение масштабирования"
    echo "4. Проверка работоспособности"
    echo "5. Мониторинг производительности"
    echo ""

    check_resources
    create_scale_config
    apply_scaling
    verify_scaling
    monitor_performance

    echo "🎉 Масштабирование завершено успешно!"
    echo ""
    echo "📊 Доступные эндпоинты:"
    echo "- Health check: http://localhost/healthz"
    echo "- Metrics: http://localhost/metrics"
    echo "- Grafana: http://localhost:3000"
    echo "- Prometheus: http://localhost:9090"
}

# Запуск основного процесса
main "$@"
