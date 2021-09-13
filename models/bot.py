from __future__ import annotations

from abc import abstractclassmethod
from dataclasses import dataclass, field
from typing import Any, Callable, ClassVar, Dict, Generic, List, Optional, Protocol, Type, TypeVar, Union

from telebot import TeleBot
from telebot.types import CallbackQuery, ForceReply, InlineKeyboardMarkup, Message, ReplyKeyboardMarkup, ReplyKeyboardRemove

from models.info import Info
from models.settings import Settings

"""
Type Variables

_S: covariant TypeVar for Protocol (which supports subclassing)
_T: invariant TypeVar for functions (used in both argument and return types)
"""
_S = TypeVar("_S", covariant=True)
_T = TypeVar("_T")
BotClass = Type["Bot"]


class Factory(Protocol[_S]):
    """
    A factory method protocol.

    Allows item to be either a class or a function, while forcing the class
    construction to return an instance.

    (Union[Type[_S], Callable[[], _S]] will NOT work because Type[_S]()
    returns Any as its metaclass and __new__ can be overridden)
    """

    @abstractclassmethod
    def __call__(self) -> _S:
        ...


@dataclass
class StepResult(Generic[_T]):
    """
    Result from a service step

    :next_step: next service step
    :last_step: is this the last service step
    :expire_all: expire all messages marked to expire
    """

    next_step: Optional[str]
    last_step: bool
    expire_all: bool = True


StatelessStepResult = StepResult[None]


@dataclass
class Service(Generic[_T]):
    """
    A bot service

    :ivar name: service name
    :ivar data: current service data
    :ivar _setup: first step after service is created
    :ivar _steps: chain of intermediate steps
    :ivar _cleanup: called before service gets destroyed
    :ivar _current_step: current step
    :ivar last_sent: messages sent last step
    :ivar _current_sent: messages sent this step
    :ivar last_expire: expiring messages sent last step
    :ivar _current_expire: expiring messages sent this step
    """

    name: str
    data: _T = field(init=False)
    _setup: Callable[[BotClass, Info, Service[_T]], StepResult[_T]]
    _steps: Dict[str, Callable[[BotClass, Info, Service[_T]], StepResult[_T]]] = field(default_factory=dict)
    _cleanup: Optional[Callable[[Service[_T]], None]] = None
    _current_step: Optional[str] = field(init=False, default=None)
    last_sent: List[Message] = field(init=False, default_factory=list)
    _current_sent: List[Message] = field(init=False, default_factory=list)
    last_expire: List[Message] = field(init=False, default_factory=list)
    _current_expire: List[Message] = field(init=False, default_factory=list)

    def handle(self, info: Info) -> StepResult[_T]:

        # Calls current step
        if self._current_step is None:
            step = self._setup
        else:
            step = self._steps.get(self._current_step)

        if step is None:
            result = StepResult[_T](next_step=self._current_step, last_step=True)
        else:
            result = step(Bot, info, self)

        # Expire messages
        if result.expire_all:
            self.expire_all()

        # Keep all unexpired messages until expire_all is called
        self.last_expire.extend(self._current_expire)
        self._current_expire = list()

        # Reset sent messages every step
        self.last_sent = list()
        self.last_sent.extend(self._current_sent)
        self._current_sent = list()

        # Move current step to next step
        if result.next_step is not None and not result.last_step:
            self._current_step = result.next_step

        # Clean service if needed
        if result.last_step and self._cleanup:
            self._cleanup(self)

        return result

    def send(
        self,
        text: Optional[str],
        chat_id: int,
        markup: Union[
            InlineKeyboardMarkup,
            ReplyKeyboardMarkup,
            ForceReply,
            ReplyKeyboardRemove,
            None,
        ] = ReplyKeyboardRemove(selective=False),
        expire: bool = False,
        **kwargs: Any,
    ) -> Message:
        """
        Send a message

        :param text: message text
        :param chat_id: chat id
        :param markup: message markup
        :param expire: whether the message should expire by next step
        """

        msg = Bot.send(text=text, chat_id=chat_id, markup=markup, **kwargs)

        self._current_sent.append(msg)

        if expire:
            self._current_expire.append(msg)

        return msg

    def resend(self, message: Message, expire: bool) -> Message:
        """
        Reend a message

        :param message: previous message
        :param expire: whether the message should expire by next step
        """
        return self.send(
            message.text,
            message.chat.id,
            message.reply_markup,
            expire=expire,
        )

    def clear_expire(self) -> None:
        """Clears the list of expiring messages"""
        self.last_expire = list()

    def expire_all(self) -> None:
        """Expire all expiring messages"""
        for to_expire in self.last_expire:
            Bot.edit(
                text="_Expired Message_",
                chat_id=to_expire.chat.id,
                message_id=to_expire.id,
                markup=None,
            )
        self.last_expire = list()


def service_factory(
    name: str,
    setup: Callable[[BotClass, Info, Service[_T]], StepResult[_T]],
    steps: Dict[str, Callable[[BotClass, Info, Service[_T]], StepResult[_T]]] = {},
    cleanup: Optional[Callable[[Service[_T]], None]] = None,
) -> Factory[Service[_T]]:
    """
    Creates a factory method to construct an empty service

    :param steps: service steps
    :param data_factory: factory method / class for service data
    """

    def factory():
        return Service[_T](name=name, _setup=setup, _steps=steps, _cleanup=cleanup)

    return factory


class Bot:
    bot: ClassVar[TeleBot]
    active_services: ClassVar[Dict[int, "Service[Any]"]] = {}

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
        """
        Start the Telegram Bot

        :param token: Telegram API key
        :param db_name: SQLite database filename
        :param dispatcher: dispatcher function (maps event to Service)
        """

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
        """
        Event (Message / CallbackQuery) handler

        :param data: Message / CallbackQuery
        """

        try:

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

        except Exception:
            if isinstance(data, Message):
                cls.send("Something went wrong :(", data.chat.id)
            else:
                cls.send("Something went wrong :(", data.message.chat.id)

    @classmethod
    def dispatcher(
        cls,
        info: Info,
        service: Optional["Service[Any]"],
    ) -> Optional["Service[Any]"]:
        """Default dispatcher"""
        return None

    @classmethod
    def send(
        cls,
        text: Optional[str],
        chat_id: int,
        markup: Union[
            InlineKeyboardMarkup,
            ReplyKeyboardMarkup,
            ForceReply,
            ReplyKeyboardRemove,
            None,
        ] = ReplyKeyboardRemove(selective=False),
        **kwargs: Any,
    ) -> Message:
        """
        Send a message

        :param text: message text
        :param chat_id: chat id
        :param markup: message markup
        """

        msg = cls.bot.send_message(
            chat_id=chat_id,
            text="" if text is None else text,
            reply_markup=markup,
            **kwargs,
        )
        return msg

    @classmethod
    def edit(
        cls,
        text: Optional[str],
        chat_id: Optional[int],
        message_id: Optional[int],
        markup: Union[
            InlineKeyboardMarkup,
            ReplyKeyboardMarkup,
            ForceReply,
            ReplyKeyboardRemove,
            None,
        ] = None,
        **kwargs: Any,
    ) -> None:
        """
        Edit a message

        :param text: message text
        :param chat_id: chat id
        :param message_id: message id
        :param markup: message markup
        """

        cls.bot.edit_message_text(
            text="" if text is None else text,
            chat_id=chat_id,
            message_id=message_id,
            reply_markup=markup,
            **kwargs,
        )
