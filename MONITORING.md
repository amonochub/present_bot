# 📊 Grafana + Alertmanager - Система мониторинга

## Обзор

Полноценная система мониторинга с красивыми дашбордами и автоматическими уведомлениями в Telegram. Все компоненты open-source без лицензионных затрат.

## 🚀 Быстрый старт

### 1. Запуск системы мониторинга

```bash
# Запуск всех сервисов
docker-compose up -d

# Проверка инициализации
./scripts/init_monitoring.sh
```

### 2. Доступные сервисы

| Сервис | URL | Логин |
|--------|-----|-------|
| 📊 **Prometheus** | http://localhost:9090 | - |
| 📈 **Grafana** | http://localhost:3000 | admin/admin123 |
| 🔔 **Alertmanager** | http://localhost:9093 | - |
| 🤖 **Bot Health** | http://localhost:8080/healthz | - |
| 📊 **Bot Metrics** | http://localhost:8080/metrics | - |

## 📊 Метрики

### Автоматически собираемые метрики

- **`bot_requests_total`** - Общее количество запросов
- **`bot_errors_total`** - Общее количество ошибок
- **`bot_latency_seconds`** - Время выполнения запросов
- **`bot_tickets_open`** - Количество открытых заявок

### Примеры запросов Prometheus

```promql
# Запросы в секунду
rate(bot_requests_total[5m])

# Ошибки в секунду
rate(bot_errors_total[5m])

# 95-й перцентиль латентности
histogram_quantile(0.95, rate(bot_latency_seconds_bucket[5m]))

# Открытые заявки
bot_tickets_open
```

## 🔔 Алерты

### Настроенные алерты

| Алерт | Условие | Действие |
|-------|---------|----------|
| **HighErrorRate** | >3 ошибок за 5 мин | Критический |
| **TooManyOpenTickets** | >10 открытых заявок | Предупреждение |
| **BotDown** | Бот недоступен 30с | Критический |
| **HighLatency** | 95% > 2 секунд | Предупреждение |

### Настройка Telegram уведомлений

1. **Создайте бота** через @BotFather
2. **Добавьте в чат/канал** для уведомлений
3. **Получите chat_id**:
   ```bash
   curl "https://api.telegram.org/bot<TOKEN>/getUpdates"
   ```
4. **Добавьте в .env**:
   ```env
   TELEGRAM_BOT_TOKEN=123456:ABC...
   TELEGRAM_CHAT_ID=-987654321
   ```

## 📈 Grafana Дашборд

### Автоматически создаваемые панели

- **Requests per Second** - График запросов в секунду
- **Errors per Second** - График ошибок в секунду
- **95th Percentile Latency** - 95-й перцентиль времени ответа
- **Open Tickets** - Количество открытых заявок

### Настройка дашборда

1. Откройте Grafana: http://localhost:3000
2. Логин: `admin/admin123`
3. Дашборд "SchoolBot Dashboard" создается автоматически
4. Для кастомизации: Edit → Export → Save to file

## 🔧 Конфигурация

### Prometheus (prometheus/prometheus.yml)

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

alerting:
  alertmanagers:
    - static_configs:
        - targets: ['alertmanager:9093']

rule_files:
  - "rules.yml"

scrape_configs:
  - job_name: 'schoolbot'
    static_configs:
      - targets: ['bot:8080']
    metrics_path: '/metrics'
    scrape_interval: 10s
```

### Alertmanager (alertmanager/alertmanager.yml)

```yaml
global:
  resolve_timeout: 1m

route:
  receiver: 'telegram'
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 2h

receivers:
- name: 'telegram'
  webhook_configs:
  - url: 'https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage'
    send_resolved: true
    http_config:
      method: POST
      headers:
        Content-Type: application/json
    body: |
      {
        "chat_id": "${TELEGRAM_CHAT_ID}",
        "parse_mode": "HTML",
        "text": "🚨 <b>{{ .GroupLabels.alertname }}</b>\n\n{{ range .Alerts }}{{ .Annotations.summary }}\n{{ .Annotations.description }}\n\n{{ end }}"
      }
```

### Grafana Provisioning

- **Datasources**: Автоматическое подключение к Prometheus
- **Dashboards**: Автоматическое создание дашборда SchoolBot

## 🧪 Тестирование

### Тест алертов

```bash
# Вызвать ошибку (HighErrorRate)
# Отправьте боту команду /crash

# Создать много заявок (TooManyOpenTickets)
# Создайте >10 заявок через интерфейс бота

# Проверить метрики
curl http://localhost:8080/metrics

# Проверить health check
curl http://localhost:8080/healthz
```

### Проверка алертов

1. **Prometheus**: http://localhost:9090/alerts
2. **Alertmanager**: http://localhost:9093
3. **Telegram**: Проверьте чат/канал

## 📊 Мониторинг производительности

### Ключевые метрики

- **Throughput**: Запросы в секунду
- **Error Rate**: Процент ошибок
- **Latency**: Время ответа (p50, p95, p99)
- **Business Metrics**: Открытые заявки

### Рекомендации по настройке

- **Scrape Interval**: 10-15 секунд для бота
- **Retention**: 7-30 дней для Prometheus
- **Alert Thresholds**: Настройте под ваши требования

## 🔍 Troubleshooting

### Проблема: Метрики не собираются

```bash
# Проверьте доступность бота
curl http://localhost:8080/metrics

# Проверьте конфигурацию Prometheus
docker-compose logs prometheus

# Проверьте сеть между контейнерами
docker-compose exec prometheus wget -qO- http://bot:8080/metrics
```

### Проблема: Алерты не отправляются

```bash
# Проверьте Alertmanager
curl http://localhost:9093/api/v1/alerts

# Проверьте переменные окружения
docker-compose exec alertmanager env | grep TELEGRAM

# Проверьте Telegram API
curl "https://api.telegram.org/bot<TOKEN>/getMe"
```

### Проблема: Grafana не подключается к Prometheus

1. Проверьте datasource в Grafana
2. Убедитесь, что Prometheus доступен
3. Проверьте сетевые настройки

## 🚀 Расширение

### Добавление новых метрик

```python
from prometheus_client import Counter, Histogram, Gauge

# Новые метрики
NEW_METRIC = Counter('bot_new_metric_total', 'Description')

# В коде
NEW_METRIC.inc()
```

### Добавление новых алертов

```yaml
# В prometheus/rules.yml
- alert: NewAlert
  expr: your_metric > threshold
  for: 1m
  labels:
    severity: warning
  annotations:
    summary: "Описание алерта"
    description: "Подробное описание"
```

### Кастомизация дашборда

1. Откройте Grafana
2. Создайте новый дашборд
3. Добавьте панели с нужными метриками
4. Export → Save to file
5. Поместите в `grafana/provisioning/dashboards/`

## 📚 Дополнительные ресурсы

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Alertmanager Documentation](https://prometheus.io/docs/alerting/latest/alertmanager/)
- [Prometheus Client Python](https://github.com/prometheus/client_python)
