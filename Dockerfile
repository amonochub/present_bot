# ---------- builder ----------
FROM python:3.11-slim AS builder
WORKDIR /app

# Копируем requirements.txt
COPY requirements.txt ./

# Устанавливаем системные зависимости для сборки
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Обновляем pip и устанавливаем зависимости
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && pip wheel --no-cache-dir -r requirements.txt -w /wheels

# ---------- runtime ----------
FROM python:3.11-bookworm
ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Копируем wheels и устанавливаем зависимости
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir --no-index --find-links=/wheels /wheels/* \
    && rm -rf /wheels

# Копируем код приложения
COPY . /app

# Делаем скрипты исполняемыми
RUN chmod +x /app/scripts/*.sh

# entrypoint применит alembic
ENTRYPOINT ["/app/scripts/run_migrations.sh"]
CMD ["python", "-m", "app.bot"]
