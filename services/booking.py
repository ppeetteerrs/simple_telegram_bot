from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, List

import pandas as pd
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
    date: pd.Timestamp = None
    start_time: pd.Timedelta = None
    end_time: pd.Timedelta = None
    n_pax: int = None
    purpose: str = None

    @property
    def record(self) -> Dict[str, Any]:
        return {
            "username": self.user.username,
            "email": self.user.email,
            "date": self.data,
            "start time": self.start_time,
            "end time": self.end_time,
            "no. of pax": self.n_pax,
            "purpose": self.purpose,
        }


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
        return "data/bookings"

    @property
    def df(self) -> pd.DataFrame:
        return pd.DataFrame.from_records(
            [booking.record for booking in self.bookings]
        ).sort_values(by="start time")


class MakeBooking(Service):
    commands = ["book"]
    data: Booking = None

    def setup(self, args: HandlerArgs) -> HandlerResult:
        """Creates empty booking object and prompt user to enter date"""

        # Creates empty booking
        self.data = Booking(user=args.user)

        if args.command is None:
            # User sent a message without selecting a date
            args.bot.send_message(
                args.message.chat.id,
                "You have yet to select a booking date.",
            )

        # Build calendar markup object and send
        calendar, step = cal(min_date=date.today()).build()
        args.bot.send_message(
            args.message.chat.id, f"Select {LSTEP[step]}", reply_markup=calendar
        )

        # next_step is None (i.e. still self.setup) since the next_step will be
        # updated when callback (cal_callback) is triggered and calls self.set_date_db
        return HandlerResult(next_step=None, success=True, last=False)

    def set_date_cb(self, bot: TeleBot, message: Message, date: date) -> None:
        """Sets booking date to the selected date and prompt for booking time"""
        self.data.date = pd.Timestamp(date)
        bot.send_message(
            message.chat.id,
            "When is the booking? (e.g. 10:00 to 13:00)",
        )
        self.set_next_step("set_time")

    def set_time(self, bot: TeleBot, message: Message, date: date) -> None:
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
                    f"Date: {str(self.data.date)}",
                    f"No. Pax: {str(self.data.n_pax)}",
                    f"Purpose: {str(self.data.purpose)}",
                ]
            ),
        )

        return HandlerResult(next_step=None, success=True, last=True)


@bot.callback_query_handler(func=cal.func())
def cal_callback(cb_query: CallbackQuery):
    """
    Calendar button callback handler
        (see documentation of python-telegram-bot-calendar)
    """

    result, key, _ = cal().process(cb_query.data)

    if not result and key:
        # Next month button pressed
        bot.edit_message_text(
            "Select booking date:",
            cb_query.message.chat.id,
            cb_query.message.message_id,
            reply_markup=key,
        )
    elif result:
        # Date selected
        id_ = cb_query.from_user.id
        service: MakeBooking = Context.get_service(id_, "book")

        # Make sure booking service is still active
        if service is not None:
            service.set_date_cb(bot, cb_query.message, result)
            bot.edit_message_text(
                f"You selected {result}.",
                cb_query.message.chat.id,
                cb_query.message.message_id,
            )
        else:
            bot.edit_message_text(
                "Booking is already cancelled. Type /book again?",
                cb_query.message.chat.id,
                cb_query.message.message_id,
            )
    else:
        bot.edit_message_text(
            "Booking request cancelled.",
            cb_query.message.chat.id,
            cb_query.message.message_id,
        )
