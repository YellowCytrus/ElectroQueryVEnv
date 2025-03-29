# run_bot.py

import os
import django

# Настраиваем Django перед использованием моделей
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lab_queue.settings')
django.setup()

# Теперь импортируем run_bot после настройки Django
from queue_site.bot import run_bot

if __name__ == "__main__":
    run_bot()