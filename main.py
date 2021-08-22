from telebot.types import Message

from config import bot
from services.booking import MakeBooking
from services.help import Help
from services.reset_email import ResetEmail
from utils.classes import Context, HandlerArgs, User

Context.add_service(Help)
Context.add_service(ResetEmail)
Context.add_service(MakeBooking)


@bot.message_handler(commands=list(Context.service_classes.keys()))
def handle_command(message: Message):

    id_: int = message.from_user.id

    user = User.load(id_)
    command: str = "start" if user is None else message.text[1:]
    args = HandlerArgs(bot=bot, user=user, message=message, command=command)
    Context.handle(args)


@bot.message_handler(content_types=["text"])
def handle_message(message: Message):

    id_: int = message.from_user.id

    user = User.load(id_)
    args = HandlerArgs(bot=bot, user=user, message=message, command=None)
    Context.handle(args)


bot.polling()
