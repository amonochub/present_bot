# KPI Метрики - Поручения директора

Система автоматического отслеживания KPI поручений директора с метриками Prometheus и дашбордами Grafana.

## 📊 Метрики

### Основные показатели

| Метрика | Описание | Тип |
|---------|----------|-----|
| `kpi_tasks_total` | Общее количество поручений | Gauge |
| `kpi_tasks_done` | Количество выполненных поручений | Gauge |
| `kpi_tasks_overdue` | Количество просроченных поручений | Gauge |

### Формулы KPI

- **Процент выполнения**: `kpi_tasks_done / kpi_tasks_total * 100`
- **Процент просрочек**: `kpi_tasks_overdue / kpi_tasks_total * 100`
- **Эффективность**: `(kpi_tasks_done - kpi_tasks_overdue) / kpi_tasks_total * 100`

## 🔄 Автоматическое обновление

### Планировщик метрик

Метрики обновляются каждые 60 секунд через фоновую корутину:

```python
# app/services/scheduler.py
async def kpi_loop():
    while True:
        # Запрос к БД
        total = await s.scalar(select(func.count()).select_from(Task))
        done = await s.scalar(select(func.count()).select_from(Task).where(Task.status == TaskStatus.COMPLETED))
        overdue = await s.scalar(select(func.count()).select_from(Task).where(Task.status == TaskStatus.PENDING, Task.deadline < date.today()))

        # Обновление метрик
        TASKS_TOTAL.set(total or 0)
        TASKS_COMPLETED.set(done or 0)
        TASKS_OVERDUE.set(overdue or 0)

        await asyncio.sleep(60)
```

### Запуск планировщика

Планировщик запускается автоматически с ботом:

```python
# app/bot.py
async def main():
    # ... инициализация ...

    # Запуск KPI планировщика
    asyncio.create_task(kpi_loop())

    # Запуск бота
    await dp.start_polling(bot)
```

## 📈 Grafana Дашборд

### Панели

1. **Всего поручений** - общее количество активных поручений
2. **Выполнено** - количество завершенных поручений
3. **Просрочено** - количество поручений с истекшим дедлайном

### Цветовая индикация

- **Зеленый** - просрочек нет (overdue = 0)
- **Красный** - есть просрочки (overdue > 0)

### Расположение

- **Файл**: `grafana/provisioning/dashboards/kpi_tasks.json`
- **URL**: http://localhost:3000 (Grafana)
- **Автозагрузка**: при старте Grafana

## 🚨 Алерты

### Правило алерта

```yaml
# prometheus/rules.yml
- alert: TooManyOverdueTasks
  expr: kpi_tasks_overdue > 3
  for: 10m
  labels:
    severity: critical
  annotations:
    summary: "Просроченных поручений > 3"
    description: "Проверить вкладку ⏱ Поручения в боте"
```

### Условия срабатывания

- **Порог**: > 3 просроченных поручений
- **Время**: 10 минут (избегает ложных срабатываний)
- **Уведомление**: Telegram через Alertmanager

## 🧪 Тестирование

### Команда /kpi_test

```bash
# В Telegram (только для директора)
/kpi_test
```

Выводит текущие значения метрик:

```
📊 Текущие KPI метрики

📋 Всего поручений: 5
✅ Выполнено: 3
⏰ Просрочено: 1

💡 Метрики обновляются каждые 60 секунд
```

### Ручное тестирование

1. **Создание просроченного поручения**:
   ```sql
   INSERT INTO tasks (title, deadline, status)
   VALUES ('Тест', '2024-01-01', 'PENDING');
   ```

2. **Проверка метрики**:
   ```bash
   curl http://localhost:8080/metrics | grep kpi_tasks
   ```

3. **Проверка алерта**:
   - Создайте 4+ просроченных поручения
   - Подождите 10 минут
   - Проверьте Telegram уведомление

## 📊 Prometheus Queries

### Основные запросы

```promql
# Всего поручений
kpi_tasks_total

# Выполнено поручений
kpi_tasks_done

# Просрочено поручений
kpi_tasks_overdue

# Процент выполнения
kpi_tasks_done / kpi_tasks_total * 100

# Процент просрочек
kpi_tasks_overdue / kpi_tasks_total * 100
```

### Графики

```promql
# Тренд выполнения за час
rate(kpi_tasks_done[1h])

# Тренд просрочек за день
rate(kpi_tasks_overdue[24h])
```

## 🔧 Конфигурация

### Переменные окружения

```bash
# Интервал обновления метрик (секунды)
KPI_UPDATE_INTERVAL=60

# Порог для алерта просрочек
KPI_OVERDUE_THRESHOLD=3
```

### Настройка планировщика

```python
# app/services/scheduler.py
UPDATE_INTERVAL = int(os.getenv("KPI_UPDATE_INTERVAL", 60))
OVERDUE_THRESHOLD = int(os.getenv("KPI_OVERDUE_THRESHOLD", 3))
```

## 📋 Интеграция с UI

### Кнопка в меню директора

```python
# app/keyboards/main_menu.py
if role == "director":
    kb = [
        [InlineKeyboardButton(text="📊 KPI", callback_data=f"{nonce}:stub")],
        [InlineKeyboardButton(text="⏱ Поручения", callback_data=f"{nonce}:director_tasks")]
    ]
```

### Inline закрытие поручений

```python
# app/handlers/director.py
@router.callback_query(lambda c: c.data.startswith("task_"))
async def toggle_task(call: CallbackQuery):
    task_id = int(call.data.split("_")[1])
    await task_repo.set_status(task_id, Status.done)
    await call.answer("✅ Выполнено!")
    # Метрика обновится через 60 секунд
```

## 🎯 Результат

После внедрения KPI системы:

- ✅ **Автоматический сбор** метрик каждые 60 секунд
- ✅ **Визуализация** в Grafana дашборде
- ✅ **Алерты** при превышении порога просрочек
- ✅ **Интеграция** с UI бота
- ✅ **Тестирование** через команду /kpi_test
- ✅ **Мониторинг** через Prometheus queries

**KPI поручений директора полностью автоматизирован!** 📊
