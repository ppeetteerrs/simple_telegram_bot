from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, ClassVar, Dict, Optional, Union

if TYPE_CHECKING:
    from models.service import Service

from telebot import TeleBot
from telebot.types import (
    CallbackQuery,
    ForceReply,
    InlineKeyboardMarkup,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

from models.message import Info
from models.settings import Settings


class Bot:
    bot: TeleBot
    active_services: ClassVar[Dict[int, "Service[Any]"]] = {}
    to_expire: Optional[Message] = None

    @classmethod
    def start(
        cls,
        token: str,
        db_name: str,
        dispatcher: Callable[
            [Info, Optional["Service[Any]"]],
            Optional["Service[Any]"],
        ] = lambda x, y: None,
    ) -> None:

        # Override default dispatcher
        if dispatcher is not None:
            setattr(cls, "dispatcher", dispatcher)

        # Set up Telegram and SQLite connections
        Settings.start(token=token, db_name=db_name)
        cls.bot = Settings.bot

        # Set up catch-all message handler
        cls.bot.message_handler(func=lambda _: True)(cls.handler)

        # Set up catch-all callback handler
        cls.bot.callback_query_handler(func=lambda _: True)(cls.handler)

        # Start polling
        cls.bot.polling()

    @classmethod
    def handler(cls, data: Union[Message, CallbackQuery]):

        # Parse message / callback info
        info = Info.parse(data)

        # Get currently active service
        active_service = cls.active_services.get(info.user_id)

        # Get next active service (usually only changes when new command is received)
        next_service = cls.dispatcher(info, active_service)

        # Update active service of the user
        if next_service is None:

            # Inform user that no service was found
            cls.active_services.pop(info.user_id, None)
            Settings.bot.send_message(info.chat_id, "Unknown service")
        else:

            # Handle info
            cls.active_services[info.user_id] = next_service
            result = cls.active_services[info.user_id].handle(info)

            # Remove active service if last step
            if result.last_step:
                cls.active_services.pop(info.user_id, None)

            # Expire last message
            if cls.to_expire is not None:
                cls.edit(
                    f"{cls.to_expire.text} (Expired)",
                    cls.to_expire.chat.id,
                    cls.to_expire.id,
                )
                cls.to_expire = None

            # Store message to be expire
            if result.should_expire:
                cls.to_expire = result.message

    @classmethod
    def dispatcher(
        cls,
        info: Info,
        service: Optional["Service[Any]"],
    ) -> Optional["Service[Any]"]:
        return None

    @classmethod
    def send(
        cls,
        chat_id: int,
        text: str,
        markup: Union[
            InlineKeyboardMarkup,
            ReplyKeyboardMarkup,
            ForceReply,
            ReplyKeyboardRemove,
        ] = ReplyKeyboardRemove(selective=False),
        /,
        **kwargs: Any,
    ) -> Message:
        return cls.bot.send_message(
            chat_id=chat_id, text=text, reply_markup=markup, **kwargs
        )

    @classmethod
    def edit(
        cls,
        text: str,
        chat_id: Optional[int] = None,
        message_id: Optional[int] = None,
        /,
        **kwargs: Any,
    ) -> None:
        if cls.last_sent is not None:

            chat_id = cls.last_sent.chat.id if chat_id is None else chat_id
            message_id = cls.last_sent.id if message_id is None else message_id

            cls.bot.edit_message_text(
                text=text,
                chat_id=chat_id,
                message_id=message_id,
                reply_markup=None,
                **kwargs,
            )
        cls.last_sent = None
