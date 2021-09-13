from __future__ import annotations

import datetime as dt
from typing import Any, Tuple, cast

from models.bot import BotClass, Service, StepResult, service_factory
from models.info import Info
from models.sql import Booking, User
from telegram_bot_calendar import WMonthTelegramCalendar as cal


def setup(bot: BotClass, info: Info, service: Service[Booking]) -> StepResult[Booking]:

    # Setup Data
    booking = Booking()
    user = User.get(info.user_id)
    user.bookings.append(booking)
    service.data = booking

    # Build calendar markup
    calendar, _ = cast(Tuple[Any, ...], cal(min_date=dt.date.today()).build())
    service.send("Select booking datee:", info.chat_id, calendar, expire=True)

    return StepResult[Booking](next_step="set_date", last_step=False)


def set_date(bot: BotClass, info: Info, service: Service[Booking]) -> StepResult[Booking]:
    # Handle callback
    if info.query is not None:

        # Process callback data
        result, key, _ = cast(Tuple[Any, ...], cal().process(info.query.data))

        if not result and key:
            # Next month selected
            bot.edit("Select booking date:", info.chat_id, info.message_id, markup=key)

            return StepResult[Booking](next_step=None, last_step=False, expire_all=False)

        elif result:
            # Date selected
            bot.edit(f"Selected {result}", info.chat_id, info.message_id)
            service.clear_expire()
            service.data.date = result

            return StepResult[Booking](next_step=None, last_step=True)

        else:
            # Cancelled
            bot.edit("Cancelled", info.chat_id, info.message_id)

            # Resend calendar
            service.resend(service.last_sent[0], expire=True)

            return StepResult[Booking](next_step=None, last_step=False)

    # Handle message
    else:
        # Resend calendar
        service.resend(service.last_sent[0], expire=True)

        return StepResult[Booking](next_step=None, last_step=False)


booking_service = service_factory("booking", setup=setup, steps={"set_date": set_date})
