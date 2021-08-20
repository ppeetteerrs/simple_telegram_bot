from telebot import TeleBot

from config.secret import TELEGRAM_KEY

bot = TeleBot(TELEGRAM_KEY, parse_mode="MARKDOWN")
