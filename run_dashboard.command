#!/bin/bash
cd "$(dirname "$0")"

echo "==============================================="
echo "   ГИДРОДИНАМИЧЕСКИЙ ДАШБОРД - ЗАПУСК"
echo "==============================================="
echo ""

echo "📦 Проверка установки Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не найден!"
    echo "📥 Установите Python с python.org и повторите запуск"
    echo ""
    read -p "Нажмите Enter для выхода..."
    exit 1
fi

echo "✅ Python обнаружен"
echo ""

echo "📦 Проверка необходимых библиотек..."
python3 -c "import dash, pandas, plotly" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "📥 Установка необходимых библиотек..."
    pip3 install dash pandas plotly
else
    echo "✅ Библиотеки уже установлены"
fi

echo ""
echo "🚀 Запуск дашборда..."
echo "🌐 Автоматическое открытие браузера..."
echo ""

# Запускаем дашборд
python3 -c "
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath('.')))

try:
    import dashboard
    print('✅ Дашборд запускается...')
    dashboard.run_dashboard(open_browser=True, debug=False)
except Exception as e:
    print(f'❌ Ошибка: {e}')
    print('💡 Проверьте наличие папки Results с данными')
    input('Нажмите Enter для выхода...')
"

echo ""
echo "✅ Дашборд завершил работу"
sleep 3