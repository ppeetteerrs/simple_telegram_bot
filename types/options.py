from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Generic, TypeVar

from telebot.types import Message

ServiceClass = TypeVar("ServiceClass")
@dataclass
class Option (Generic[ServiceClass]):
    service: ServiceClass
    question: str
    validate: Callable[[ServiceClass], bool]
    timeout: int

Option(1, "", lambda x: not not x, 1)


class TextOption:
    pass

class CallbackOption:
    pass
