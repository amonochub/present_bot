# ---------- builder ----------
FROM python:3.11-slim AS builder
WORKDIR /app
# 1) ускоряем layer-кэш: копируем только зависимости
COPY requirements.txt ./
RUN apt-get update && apt-get install -y --no-install-recommends build-essential gcc libpq-dev \
 && pip install --upgrade pip \
 && pip wheel --no-cache-dir --no-deps -r requirements.txt -w /wheels \
 && apt-get purge -y build-essential gcc libpq-dev && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

# ---------- runtime ----------
FROM python:3.11-bookworm
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir --no-index --find-links=/wheels /wheels/*
COPY . /app

# entrypoint применит alembic
ENTRYPOINT ["/app/scripts/run_migrations.sh"]
CMD ["python", "-m", "app.bot"]
