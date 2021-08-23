from __future__ import annotations

from abc import abstractclassmethod
from dataclasses import dataclass, field
from typing import Callable, Dict, Generic, Optional, Protocol, TypeVar

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


@dataclass
class Service(Generic[_T]):
    """
    A bot service

    :ivar data: current service data
    :ivar setup: first step after service is created
    :ivar steps: chain of intermediate steps
    :ivar cleanup: called before service gets destroyed
    :ivar current_step: current step
    """

    data: _T
    setup: Callable[[Bot, Info], StepResult[_T]]
    steps: Dict[str, Callable[[Bot, Info, _T], StepResult[_T]]] = field(
        default_factory=dict
    )
    cleanup: Optional[Callable[[Service[_T]], None]] = None
    current_step: Optional[str] = field(init=False, default=None)

    def handle(self, info: Info) -> StepResult[_T]:
        # Get current step
        if self.current_step is None:
            step = self.setup
            result = step(Bot(), info)
        else:
            step = self.steps.get(self.current_step)

            if step is None:
                result = StepResult[_T](
                    next_step=self.current_step, last_step=True
                )
            else:
                result = step(Bot(), info, self.data)

        # Update data
        if result.data is not None:
            self.data = result.data

        # Move current step to next step
        if result.next_step is not None and not result.last_step:
            self.current_step = result.next_step

        # Clean service if needed
        if result.last_step and self.cleanup:
            self.cleanup(self)

        return result


def service_factory(
    setup: Callable[[Bot, Info], StepResult[_T]],
    steps: Dict[str, Callable[[Bot, Info, _T], StepResult[_T]]] = {},
    cleanup: Optional[Callable[[Service[_T]], None]] = None,
    data_factory: Factory[_T] = lambda: None,
) -> Factory[Service[_T]]:
    """
    Creates a factory method to construct an empty service

    :param steps: service steps
    :param data_factory: factory method / class for service data
    """

    def factory():
        return Service[_T](
            setup=setup, steps=steps, cleanup=cleanup, data=data_factory()
        )

    return factory
