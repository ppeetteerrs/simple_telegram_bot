from __future__ import annotations

import re

from models.bot import BotClass
from models.message import Info
from models.service import Service, StepResult, service_factory
from models.sql import User


def setup(bot: BotClass, info: Info, service: Service[User]) -> StepResult[User]:
    service.send(info.chat_id, "What is your email?")

    service.data = User(username="" if info.username is None else info.username, id=info.user_id)

    return StepResult[User](next_step="set_email", last_step=False)


def set_email(bot: BotClass, info: Info, service: Service[User]) -> StepResult[User]:

    # Check email
    email = "" if info.data is None else info.data
    regex = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"

    if re.fullmatch(regex, email) and "ntu.edu.sg" in email:
        service.data.email = email
        service.data.save()

        service.send(info.chat_id, "Registered")

        return StepResult[User](
            next_step=None,
            last_step=True,
        )
    else:
        service.send(chat_id=info.chat_id, text="Invalid email")

        return StepResult[User](
            next_step=None,
            last_step=False,
        )


email_service = service_factory("email", setup=setup, steps={"set_email": set_email})
