from typing import Any, Optional

from config.secret import DB_NAME, TELEGRAM_KEY
from models.bot import Bot
from models.message import Info
from models.service import Service
from services.booking import booking_service
from services.reset_email import User, email_service


def dispatcher(info: Info, service: Optional[Service[Any]]):
    user_record = User.find(info.user_id)

    if user_record is None:
        if service is not None and service.name == "email":
            return service
        else:
            return email_service()
    else:
        if info.data is not None and info.data.startswith("/") and info.query is None:
            return booking_service()
        else:
            return service


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
