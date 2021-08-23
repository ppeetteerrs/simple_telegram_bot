from abc import abstractclassmethod
from dataclasses import dataclass
from functools import partial, wraps
from inspect import getargs, getargspec, getfullargspec
from types import FunctionType
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    Optional,
    Protocol,
    Tuple,
    Type,
    TypeVar,
    Union,
)


def wrap(f: FunctionType):
    @wraps(f)
    def wrapper(*args: Any):
        n_args = f.__code__.co_argcount
        return f(*args[:n_args])

    return wrapper


def func(arg1: int, arg2: int, *args: Any):
    print(arg1, arg2)


def hmmm(arg: Callable[[int, int], Any], arg1: int, arg2: int):
    arg(arg1, arg2)


hmmm(func, 1, 2)
