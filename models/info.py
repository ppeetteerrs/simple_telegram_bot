from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Union

from telebot.types import CallbackQuery, Message


@dataclass
class Info:
    """
    Event info class

    :ivar id: message / callback query id
    :ivar chat_id: chat id
    :ivar message_id: message id / callback query sent message id
    :ivar user_id: user id
    :ivar username: username

    :ivar kind: content type / callback
    :ivar data: message text / callback data
    :ivar sent: message sent time / callback query sent message sent time
    :ivar message: message / callback query sent message
    :ivar query: None / callback query
    """

    id: int
    chat_id: int
    message_id: int
    user_id: int
    username: Optional[str]

    kind: str
    data: Optional[str]
    sent: datetime
    message: Optional[Message] = None
    query: Optional[CallbackQuery] = None

    @classmethod
    def parse(cls, item: Union[Message, CallbackQuery]):
        """
        Parses a Message / CallbackQuery into Info

        :param item: Message / CallbackQuery
        """

        if isinstance(item, Message):
            item.text
            return cls(
                id=item.id,
                chat_id=item.chat.id,
                message_id=item.message_id,
                user_id=item.from_user.id,
                username=item.from_user.username,
                kind=item.content_type,
                data=item.text,
                sent=datetime.fromtimestamp(item.date),
                message=item,
            )
        else:
            return cls(
                id=item.id,
                chat_id=item.message.chat.id,
                message_id=item.message.id,
                user_id=item.from_user.id,
                username=item.from_user.username,
                kind="callback",
                data=item.data,
                sent=datetime.fromtimestamp(item.message.date),
                message=item.message,
                query=item,
            )
