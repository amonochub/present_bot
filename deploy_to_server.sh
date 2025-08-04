#!/bin/bash

# Скрипт для развертывания исправлений Ghostscript на оба бота
set -e

echo "🚀 Развертывание исправлений Ghostscript на оба бота..."

# Подключение к серверу и обновление обоих ботов
ssh root@89.169.38.246 << 'EOF'

echo "📦 Обновляем telegram-file-bot..."
cd /srv/bots/telegram-file-bot

# Получаем последние изменения
git fetch origin
git pull origin main

# Проверяем наличие исправлений в коде
if grep -q "output_type=\"pdf\"" app/services/ocr_service.py 2>/dev/null; then
    echo "✅ Исправления Ghostscript найдены в telegram-file-bot"
else
    echo "❌ Исправления Ghostscript НЕ найдены в telegram-file-bot"
    echo "🔧 Применяем исправления вручную..."
    
    # Создаем резервную копию
    cp app/services/ocr_service.py app/services/ocr_service.py.backup
    
    # Применяем исправления
    sed -i 's/pdf2image.convert_from_path(pdf_path)/pdf2image.convert_from_path(pdf_path, output_type="pdf")/g' app/services/ocr_service.py
    
    # Добавляем fallback обработку
    cat >> app/services/ocr_service.py << 'EOL'

# Fallback обработка при ошибках Ghostscript
def process_pdf_with_fallback(pdf_path: str) -> List[Image.Image]:
    """Обработка PDF с fallback при ошибках Ghostscript"""
    try:
        return pdf2image.convert_from_path(pdf_path, output_type="pdf")
    except Exception as e:
        print(f"Ошибка Ghostscript: {e}")
        print("Применяем fallback с force_ocr=True...")
        return pdf2image.convert_from_path(pdf_path, force_ocr=True)
EOL
fi

# Перезапускаем telegram-file-bot
echo "🔄 Перезапускаем telegram-file-bot..."
docker-compose down
docker-compose up -d

echo "📦 Обновляем present-bot..."
cd /srv/bots/present-bot

# Получаем последние изменения
git fetch origin
git pull origin main

# Проверяем наличие исправлений в коде present-bot
if grep -q "output_type=\"pdf\"" app/services/pdf_factory.py 2>/dev/null; then
    echo "✅ Исправления Ghostscript найдены в present-bot"
else
    echo "❌ Исправления Ghostscript НЕ найдены в present-bot"
    echo "🔧 Применяем исправления вручную..."
    
    # Создаем резервную копию
    cp app/services/pdf_factory.py app/services/pdf_factory.py.backup
    
    # Применяем исправления для present-bot
    sed -i 's/pdf2image.convert_from_path(pdf_path)/pdf2image.convert_from_path(pdf_path, output_type="pdf")/g' app/services/pdf_factory.py
    
    # Добавляем fallback обработку для present-bot
    cat >> app/services/pdf_factory.py << 'EOL'

# Fallback обработка при ошибках Ghostscript для present-bot
def process_pdf_with_fallback_present(pdf_path: str) -> List[Image.Image]:
    """Обработка PDF с fallback при ошибках Ghostscript для present-bot"""
    try:
        return pdf2image.convert_from_path(pdf_path, output_type="pdf")
    except Exception as e:
        print(f"Ошибка Ghostscript в present-bot: {e}")
        print("Применяем fallback с force_ocr=True...")
        return pdf2image.convert_from_path(pdf_path, force_ocr=True)
EOL
fi

# Перезапускаем present-bot
echo "🔄 Перезапускаем present-bot..."
docker-compose down
docker-compose up -d

# Проверяем статус обоих ботов
echo "📊 Проверяем статус ботов..."
sleep 15

echo "📊 Статус telegram-file-bot:"
docker logs telegram-file-bot_bot_1 --tail 5

echo "📊 Статус present-bot:"
docker logs present-bot_bot_1 --tail 5

echo "✅ Развертывание завершено для обоих ботов!"
EOF

echo "🎉 Исправления Ghostscript развернуты на оба бота!"
echo "📱 Теперь PDF файлы должны обрабатываться без ошибок Ghostscript в обоих ботах" 