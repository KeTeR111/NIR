#!/bin/bash

# Автокоммит скрипт для git
# Запускается каждые 5 минут через cron

cd /Users/andrey/Desktop/NIR

# Проверяем есть ли изменения
if [[ -n $(git status --porcelain) ]]; then
    # Добавляем все изменения
    git add -A

    # Создаем коммит с датой и временем
    git commit -m "Автокоммит: $(date '+%Y-%m-%d %H:%M:%S')"

    echo "$(date): Коммит создан" >> /Users/andrey/Desktop/NIR/.auto_commit.log
else
    echo "$(date): Нет изменений" >> /Users/andrey/Desktop/NIR/.auto_commit.log
fi
