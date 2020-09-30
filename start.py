from dotenv import load_dotenv
import telebot
import os

import hogart_bot

if __name__ == "__main__":
    load_dotenv()
    telegram_token: str = os.getenv("TELEGRAM_TOKEN")
    botan_key: str = os.getenv("BOTAN_KEY")
    yandex_key: str = os.getenv("YANDEX_TOKEN")
    bot = telebot.TeleBot(telegram_token)
    hogart_bot.add_handlers_to_bot(bot, telegram_token, botan_key, yandex_key)
    bot.polling()
