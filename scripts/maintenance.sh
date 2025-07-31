#!/usr/bin/env bash
set -eo pipefail
KEEP_DAYS=${KEEP_DAYS:-14}

echo "[maintenance] Удаляем старше $KEEP_DAYS дн."

# 1) gzip-дампы БД
find /backups -type f -name "*.sql.gz" -mtime +$KEEP_DAYS -delete

# 2) GlitchTip логи (>50 МБ)
find /var/lib/glitchtip -type f -size +50M -mtime +$KEEP_DAYS -delete 2>/dev/null || true

# 3) Docker-логи контейнера bot (>100 МБ)
LOGF=/var/lib/docker/containers
find "$LOGF" -type f -name "*-json.log" -size +100M -print -exec truncate -s 0 {} \;

echo "[maintenance] Готово $(date)"
