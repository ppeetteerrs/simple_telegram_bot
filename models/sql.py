from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from typing import Any, List, Optional, Type, TypeVar

from sqlalchemy.orm import relationship
from sqlalchemy.orm.query import Query
from sqlalchemy.sql.schema import Column, ForeignKey
from sqlalchemy.sql.sqltypes import Date, Integer, String
from sqlalchemy.sql.type_api import TypeEngine

from models.settings import Settings, sql_map

_T = TypeVar("_T")


def Id(**kwargs: Any):
    return field(init=False, **kwargs, metadata={"sa": Column(Integer, primary_key=True)})


def Field(field_type: TypeEngine[Any], **kwargs: Any):
    return field(
        init=False,
        default=None,
        **kwargs,
        metadata={"sa": Column(field_type)},
    )


def FKey(key: str, **kwargs: Any):
    return field(
        init=False,
        default=None,
        **kwargs,
        metadata={"sa": Column(ForeignKey(key))},
    )


def Relationship(table: str, backref: str, **kwargs: Any) -> List[Any]:
    field_: List[Any] = field(
        init=False,
        default_factory=list,
        **kwargs,
        metadata={"sa": relationship(table, backref=backref)},
    )
    return field_


@dataclass
class SQLMixin:
    """SQLAlchemy SQL Mixin class

    :cvar __tablename___: defaults to lowercase of class name
    :cvar query: querys a record
    :cvar find: find a record by ID
    :cvar get: get a record by ID (when record is already found)

    :ivar save: save object to db file
    :ivar reset: refresh object instance
    :ivar delete delete obect instance
    """

    @classmethod
    @property
    def __tablename__(cls) -> str:
        return cls.__name__.lower()

    __sa_dataclass_metadata_key__ = "sa"

    @classmethod
    def query(cls: Type[_T]) -> "Query[_T]":
        return Settings.session.query(cls)

    @classmethod
    def find(cls: Type[_T], id: Any) -> Optional[_T]:
        return Settings.session.query(cls).get(id)

    @classmethod
    def get(cls: Type[_T], id: Any) -> _T:
        record = Settings.session.query(cls).get(id)
        if record is None:
            raise ValueError("get should only be used when record 100% exists")
        return record

    def save(self):
        Settings.session.add(self)
        Settings.session.commit()

    def reset(self):
        Settings.session.refresh(self)

    def delete(self):
        Settings.session.delete(self)
        Settings.session.commit()


@sql_map
@dataclass
class User(SQLMixin):
    id: int = Id()
    username: Optional[str] = Field(String(150))
    email: Optional[str] = Field(String(150))
    bookings: List[Booking] = Relationship("Booking", "user")


@sql_map
@dataclass
class Booking(SQLMixin):
    id: int = Id()
    user_id: Optional[int] = FKey("user.id")
    date: Optional[dt.date] = Field(Date())
    n_pax: Optional[int] = Field(Integer())
    purpose: Optional[str] = Field(String(500))
