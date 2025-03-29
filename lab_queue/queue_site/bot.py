# queue_site/bot.py

import json
import os
from telegram.ext import Application, CommandHandler, CallbackContext
from telegram import Update
import asyncio
from .models import RegistrationToken
from asgiref.sync import sync_to_async

# Укажем абсолютный путь
CHAT_IDS_FILE = '/home/cytr/PycharmProjects/ElectroQueryVEnv/lab_queue/chat_ids.json'

def load_chat_ids():
    if os.path.exists(CHAT_IDS_FILE):
        with open(CHAT_IDS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_chat_ids(chat_ids):
    try:
        with open(CHAT_IDS_FILE, 'w') as f:
            json.dump(chat_ids, f)
        print(f"Successfully saved chat_ids to {CHAT_IDS_FILE}")
    except Exception as e:
        print(f"Error saving chat_ids: {str(e)}")

chat_ids = load_chat_ids()

async def start(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    telegram_username = update.message.from_user.username
    args = context.args

    print(f"Received /start from user: {telegram_username}, args: {args}")

    if not telegram_username:
        print("User has no Telegram username")
        await update.message.reply_text("У вас нет Telegram username. Пожалуйста, установите его в настройках Telegram.")
        return

    chat_ids[telegram_username] = chat_id
    save_chat_ids(chat_ids)
    print(f"Updated chat_ids: {chat_ids}")

    if not args:
        print("No token provided in /start command")
        await update.message.reply_text("Пожалуйста, используйте ссылку с сайта для активации бота.")
        return

    token = args[0]
    print(f"Looking for RegistrationToken with token: {token}")
    try:
        registration_token = await sync_to_async(RegistrationToken.objects.get)(token=token, is_used=False)
        print(f"Found RegistrationToken: {registration_token}")

        registration_token.telegram_username = f"@{telegram_username}"
        await sync_to_async(registration_token.save)()
        print(f"Updated RegistrationToken with telegram_username: {registration_token.telegram_username}")

        await update.message.reply_text("Бот успешно активирован! Вернитесь на сайт и завершите регистрацию.")
    except RegistrationToken.DoesNotExist:
        print(f"Token {token} not found in database or already used")
        await update.message.reply_text("Неверный токен или токен уже использован. Пожалуйста, попробуйте снова.")
        return
    except Exception as e:
        print(f"Error updating RegistrationToken: {str(e)}")
        await update.message.reply_text("Произошла ошибка. Пожалуйста, попробуйте снова.")
        return

def run_bot():
    try:
        bot_token = '7951386321:AAHxpTDG6yhTRl9ap2uazpy7vX_-9mv1HPw'
        print("Building bot application...")
        app = Application.builder().token(bot_token).build()
        print("Adding command handler...")
        app.add_handler(CommandHandler("start", start))
        print("Starting bot polling...")
        app.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        print(f"Error in run_bot: {str(e)}")