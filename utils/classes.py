import traceback
from dataclasses import dataclass
from typing import Callable, ClassVar, Dict, List, Optional, Type

from telebot import TeleBot
from telebot.types import Message

from utils.dataclass import DataClass, User


@dataclass(frozen=True)
class HandlerResult:
    """
    Message handler result.
        next_step: method to be called when next message arrives
        success: whether handling was successful
        last: whether method is the last operation for the command
    """

    next_step: str
    success: bool = True
    last: bool = False


@dataclass(frozen=True)
class HandlerArgs:
    """Message handler arguments."""

    bot: TeleBot
    user: Optional[User]
    message: Message
    command: str


Handler = Callable[[HandlerArgs], HandlerResult]


@dataclass
class Service:
    """
    A bot service
        commands: list of commands that maps to this service
        data: data cache (for storage across multiple messages / users / callbacks)
        next_step: next method handler to be called

        setup: handler function to be called when command is typed in
        set_next_step: self-explanatory
        next: calls self.next_step
    """

    commands: ClassVar[List[str]]
    data: DataClass = None
    next_step: Handler = None

    def setup(self, args: HandlerArgs) -> HandlerResult:
        return HandlerResult(next_step=None, success=False, last=True)

    def set_next_step(self, next_step: Optional[str]) -> None:
        if next_step is None:
            self.next_step = None
        else:
            self.next_step = getattr(self, next_step)

    def next(self, args: HandlerArgs) -> HandlerResult:
        if self.next_step is None:
            self.next_step = self.setup

        try:
            result = self.next_step(args)
        except Exception:
            print(traceback.format_exc(), file=open("logs.txt", "w"))
            result = HandlerResult(next_step=None, success=False, last=True)
            args.bot.send_message(
                args.message.chat.id, "Something went wrong :("
            )

        # Only move on to next step when handler succeeds
        if result.success:
            if result.next_step is None:
                self.next_step = None
            else:
                self.next_step = getattr(self, result.next_step)

        return result


class Context:
    """
    Bot context
        service_classes: mapping from command to service
        user_data: mapping from user ID to active service

        add_service: register a new service
        handle: handle a message
        get_service: helper function to get active service of a user
    """

    service_classes: Dict[str, Type[Service]] = {}
    user_data: Dict[str, Service] = {}

    @classmethod
    def add_service(cls, service_class: Type[Service]) -> None:
        for command in service_class.commands:
            cls.service_classes[command] = service_class

    @classmethod
    def handle(cls, args: HandlerArgs) -> bool:

        # Get currently active service for user
        id_ = args.message.from_user.id
        current_service = cls.user_data.get(id_)
        command = (
            args.command if args.command in cls.service_classes else "help"
        )

        # Start new service if no command / no active service
        if current_service is None or args.command is not None:
            current_service = cls.user_data[id_] = cls.service_classes[
                command
            ]()

        # Run 1 step in the service and wait for next message
        result = current_service.next(args)

        # Clear active service on last operation
        if result.last:
            cls.user_data.pop(id_)

        return result.success

    @classmethod
    def get_service(cls, id_: int, command: str) -> Optional[Service]:
        service = cls.user_data.get(id_)
        if service is None or command not in service.commands:
            return None
        else:
            return service
