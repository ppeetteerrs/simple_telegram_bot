from dataclasses import dataclass, field
from typing import Any, Optional, Type, TypeVar

from sqlalchemy.orm.query import Query
from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.sqltypes import Integer, String

from models.settings import Settings, sql_map

_T = TypeVar("_T")


@dataclass
class SQLMixin:
    @classmethod
    @property
    def __tablename__(cls) -> str:
        return cls.__name__.lower()

    __sa_dataclass_metadata_key__ = "sa"

    @classmethod
    def query(cls: Type[_T]) -> "Query[_T]":
        return Settings.session.query(cls)

    @classmethod
    def by_id(cls: Type[_T], id: Any) -> Optional[_T]:
        return Settings.session.query(cls).get(id)

    def save(self):
        Settings.session.add(self)
        Settings.session.commit()

    def reset(self):
        Settings.session.refresh(self)

    def delete(self):
        Settings.session.delete(self)
        Settings.session.commit()
