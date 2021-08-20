from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import List

from config import bot
from telebot import TeleBot
from telebot.types import CallbackQuery, Message
from telegram_bot_calendar import LSTEP
from telegram_bot_calendar import WMonthTelegramCalendar as cal
from utils.classes import (
    Context,
    DataClass,
    HandlerArgs,
    HandlerResult,
    Service,
    User,
)


@dataclass
class Booking(DataClass):
    user: User
    date: date = None
    n_pax: int = None
    purpose: str = None


@dataclass
class Bookings(DataClass):
    date: date
    bookings: List[Booking]

    @property
    def n_pax(self) -> int:
        return sum([booking.n_pax for booking in self.bookings])

    @property
    def key(self) -> date:
        return self.date

    @classmethod
    def dir(cls) -> str:
        return Path("data/bookings")


class MakeBooking(Service):
    commands = ["book"]
    data: Booking = None

    def setup(self, args: HandlerArgs) -> HandlerResult:

        self.data = Booking(user=args.user)

        calendar, step = cal(min_date=date.today()).build()

        args.bot.send_message(
            args.message.chat.id, f"Select {LSTEP[step]}", reply_markup=calendar
        )

        return HandlerResult(next_step=None, success=True, last=False)

    def set_date_cb(self, bot: TeleBot, message: Message, date: date) -> None:
        self.data.date = date
        bot.send_message(message.chat.id, "What is the number of pax?")
        self.set_next_step("set_n_pax")

    def set_n_pax(self, args: HandlerArgs) -> HandlerResult:

        self.data.n_pax = int(args.message.text)
        args.bot.send_message(args.message.chat.id, "What is the purpose?")

        return HandlerResult(next_step="set_purpose", success=True, last=False)

    def set_purpose(self, args: HandlerArgs) -> HandlerResult:

        self.data.purpose = args.message.text
        args.bot.send_message(
            args.message.chat.id,
            "\n".join(
                [
                    "Booking is made!",
                    f"*Date*: {str(self.data.date)}",
                    f"No. Pax: {str(self.data.n_pax)}",
                    f"Purpose: {str(self.data.purpose)}",
                ]
            ),
        )

        return HandlerResult(next_step=None, success=True, last=True)


@bot.callback_query_handler(func=cal.func())
def cal_callback(cb_query: CallbackQuery):
    result, key, step = cal().process(cb_query.data)
    id_ = cb_query.from_user.id

    if not result and key:
        bot.edit_message_text(
            f"Select {LSTEP[step]}",
            cb_query.message.chat.id,
            cb_query.message.message_id,
            reply_markup=key,
        )
    elif result:
        service: MakeBooking = Context.get_service(id_, "book")

        if service is not None:
            service.set_date_cb(bot, cb_query.message, result)

        bot.edit_message_text(
            f"You selected {result}",
            cb_query.message.chat.id,
            cb_query.message.message_id,
        )
