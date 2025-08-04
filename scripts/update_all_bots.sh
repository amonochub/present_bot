#!/bin/bash
set -e

echo "$(date): 🔄 Начинаем автообновление ботов..." | tee -a /var/log/bot-updates.log

# Функция безопасного обновления
safe_update() {
    local bot_name=$1
    local bot_path=$2
    
    echo "📦 Обновляем $bot_name..." | tee -a /var/log/bot-updates.log
    cd "$bot_path"
    
    # Получаем изменения
    git fetch origin
    LOCAL=$(git rev-parse HEAD)
    REMOTE=$(git rev-parse origin/main)
    
    if [ "$LOCAL" != "$REMOTE" ]; then
        echo "📥 Найдены обновления для $bot_name" | tee -a /var/log/bot-updates.log
        
        # Сохраняем локальные изменения
        git stash push -m "Auto-stash before update"
        
        # Обновляем
        git reset --hard origin/main
        
        # Возвращаем локальные изменения если они были
        git stash pop 2>/dev/null || echo "No stash to restore"
        
        # Специальные исправления для каждого бота
        if [[ "$bot_name" == *"present-bot"* ]]; then
            # Исправляем порт Redis для present-bot
            sed -i 's/6379:6379/6380:6379/' docker-compose.yml
            # Отключаем seed_demo
            find app/ -name '*.py' -exec sed -i 's/.*seed_demo.*/#&/g' {} \; 2>/dev/null || true
        fi
        
        # Перезапускаем с очисткой
        docker-compose down 2>/dev/null || true
        sleep 2
        docker-compose up -d --build
        
        echo "✅ $bot_name успешно обновлен" | tee -a /var/log/bot-updates.log
    else
        echo "📋 $bot_name уже актуален" | tee -a /var/log/bot-updates.log
    fi
}

# Обновляем боты
safe_update 'telegram-file-bot' '/srv/bots/telegram-file-bot'
safe_update 'present-bot' '/srv/bots/present-bot'

echo "$(date): ✅ Автообновление завершено" | tee -a /var/log/bot-updates.log
echo "---" >> /var/log/bot-updates.log 