from typing import Any, Optional

from telebot.types import Animation

from config.secret import DB_NAME, TELEGRAM_KEY
from models.bot import Bot
from models.message import Info
from models.service import Service, StatelessStepResult, service_factory

default_service = service_factory(
    steps=lambda bot, info: StatelessStepResult(
        message=bot.send(info.chat_id, "hi there")
    )
)


def dispatcher(info: Info, service: Optional[Service[Any]]):
    return None


Bot.start(TELEGRAM_KEY, DB_NAME, dispatcher=dispatcher)


# Settings.start(TELEGRAM_KEY, DB_NAME)


# @Settings.bot.message_handler(regexp=".*")
# def handle_command(message: Message):

#     Settings.bot.send_message(message.chat.id, "hi")


# Settings.bot.polling()


# @bot.message_handler(commands=list(Context.service_classes.keys()))
# def handle_command(message: Message):

#     id_: int = message.from_user.id

#     user = User.load(id_)
#     command: str = "start" if user is None else message.text[1:]
#     args = HandlerArgs(bot=bot, user=user, message=message, command=command)
#     Context.handle(args)


# @bot.message_handler(content_types=["text"])
# def handle_message(message: Message):

#     id_: int = message.from_user.id

#     user = User.load(id_)
#     args = HandlerArgs(bot=bot, user=user, message=message, command=None)
#     Context.handle(args)
