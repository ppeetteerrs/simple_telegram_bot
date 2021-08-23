from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Union

from telebot.types import CallbackQuery, Message


@dataclass
class Info:
    id: int
    chat_id: int
    user_id: int
    username: Optional[str]

    kind: str
    data: Optional[str]
    sent: datetime
    message: Optional[Message] = None
    query: Optional[CallbackQuery] = None

    @classmethod
    def parse(cls, item: Union[Message, CallbackQuery]):
        if isinstance(item, Message):
            return cls(
                id=item.id,
                chat_id=item.chat.id,
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
                user_id=item.from_user.id,
                username=item.from_user.username,
                kind="callback",
                data=item.data,
                sent=datetime.fromtimestamp(item.message.date),
                message=item.message,
                query=item,
            )
