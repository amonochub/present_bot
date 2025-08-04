# ---------- builder ----------
FROM python:3.11-slim AS builder
WORKDIR /app

# Устанавливаем системные зависимости для сборки
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libpq-dev \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Копируем requirements.txt
COPY requirements.txt ./

# Обновляем pip и устанавливаем зависимости
RUN pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt \
    && pip wheel --no-cache-dir -r requirements.txt -w /wheels

# ---------- runtime ----------
FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PATH="/app/venv/bin:$PATH"

WORKDIR /app

# Устанавливаем runtime зависимости
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Создаем виртуальное окружение
RUN python -m venv /app/venv

# Копируем wheels и устанавливаем зависимости
COPY --from=builder /wheels /wheels
RUN /app/venv/bin/pip install --no-cache-dir --no-index --find-links=/wheels /wheels/* \
    && rm -rf /wheels

# Копируем код приложения
COPY . /app

# Делаем скрипты исполняемыми
RUN chmod +x /app/scripts/*.sh /app/run_bot.py

# Создаем пользователя для безопасности
RUN groupadd -r botuser && useradd -r -g botuser botuser
RUN chown -R botuser:botuser /app
USER botuser

# Проверяем здоровье контейнера
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# entrypoint применит alembic
ENTRYPOINT ["/app/scripts/run_migrations.sh"]
CMD ["python", "-m", "app.bot"]
