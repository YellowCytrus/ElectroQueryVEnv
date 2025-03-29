# import redis
#
# # Подключение к Redis
# r = redis.Redis(host='127.0.0.1', port=6379)
#
# # Проверка подключения
# try:
#     response = r.ping()
#     print("Connected to Redis:", response)
# except redis.exceptions.ConnectionError as e:
#     print("Failed to connect to Redis:", e)


# test_telegram.py

from telegram import Bot
import asyncio

async def test_get_chat():
    bot_token = 'YOUR_BOT_TOKEN'  # Замени на реальный токен
    bot = Bot(token=bot_token)
    try:
        chat = await bot.get_chat('@yellow_cytrus')
        print(f"Chat ID: {chat.id}")
    except Exception as e:
        print(f"Ошибка: {str(e)}")

# Запускаем асинхронный код
asyncio.run(test_get_chat())