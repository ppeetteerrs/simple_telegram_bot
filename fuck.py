from dataclasses import dataclass
from typing import (
    Any,
    Callable,
    ClassVar,
    Dict,
    Final,
    Generic,
    List,
    Tuple,
    Type,
    TypedDict,
    TypeVar,
)

from telebot.types import Message


class Welps(TypedDict):
    key1: str


def weelll(arg: Welps):
    return arg


weelll({"key1": "i", "jey3": 1})
