from __future__ import annotations

from abc import abstractclassmethod
from dataclasses import dataclass, field
from functools import wraps
from typing import (
    Any,
    Callable,
    Dict,
    Final,
    Generic,
    Optional,
    Protocol,
    TypeVar,
    Union,
    cast,
)

from telebot.types import Message

from models.bot import Bot
from models.message import Info

"""
Type Variables

_S: covariant TypeVar for Protocol (which supports subclassing)
_T: invariant TypeVar for functions (used in both argument and return types)
"""
_S = TypeVar("_S", covariant=True)
_T = TypeVar("_T")


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

    :ivar message: message sent to user
    :ivar expire_last: expire the last message sent if it contains markup
    :next_step: next service step
    :last_step: is this the last service step
    """

    last_step: bool = True
    next_step: Optional[str] = None
    should_expire: bool = False
    data: Optional[_T] = None
    message: Optional[Message] = None


StatelessStepResult = StepResult[None]

"""
Step types

Union[Dict[X, Y], Dict[X, Z]] works but Dict[X, Union[Y,Z]]
doesn't because Dict are mutable and should only contain one value type
"""
StatelessStep = Callable[[Bot, Info], StepResult[_T]]
StatefulStep = Callable[[Bot, Info, _T], StepResult[_T]]

StepsArg = Union[
    Dict[str, StatelessStep[_T]],
    Dict[str, StatefulStep[_T]],
]

Steps = Dict[str, StatefulStep[_T]]

"""
Dirty trick to make sure all steps can be treated as StatefulStep
"""


def wrap_step(f: Union[StatelessStep[_T], StatefulStep[_T]]):
    @wraps(f)
    def wrapper(*args: Any):
        n_args = f.__code__.co_argcount
        return f(*args[:n_args])

    stateful_wrapper = cast(StatefulStep[_T], wrapper)
    return stateful_wrapper


def default_handle(bot: Bot, info: Info):
    msg = bot.send(info.chat_id, "noway")

    return StatelessStepResult(
        message=msg, should_expire=False, next_step="setup", last_step=True
    )


@dataclass
class Service(Generic[_T]):
    """
    A bot service

    :ivar data: current service data
    :ivar steps: dictionary of steps in the service (starts from "setup")
    :ivar current_step: current step
    """

    data: _T
    steps: Final[Steps[_T]] = field(init=True, default_factory=dict)
    current_step: str = field(init=False, default="setup")

    def handle(self, info: Info) -> StepResult[_T]:
        # Get current step
        step = self.steps.get(self.current_step)

        # Execute current step
        if step is None:
            result = StepResult[_T](next_step=self.current_step, last_step=True)
        else:
            result = step(Bot(), info, self.data)

        # Update data
        if result.data is not None:
            self.data = result.data

        # Move current step to next step
        if result.next_step is not None:
            self.current_step = result.next_step

        return result


def service_factory(
    steps: Union[StatelessStep[_T], StepsArg[_T]],
    data_factory: Factory[_T] = lambda: None,
) -> Factory[Service[_T]]:
    """
    Creates a factory method to construct an empty service

    :param steps: service steps
    :param data_factory: factory method / class for service data
    """
    if isinstance(steps, dict):
        if "setup" not in steps:
            raise AssertionError("setup step is missing.")
        parsed_steps = {name: wrap_step(step) for name, step in steps.items()}
    else:
        parsed_steps = {"setup": wrap_step(steps)}

    def factory():
        return Service[_T](data=data_factory(), steps=parsed_steps)

    return factory
