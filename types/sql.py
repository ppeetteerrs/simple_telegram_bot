from __future__ import annotations

from dataclasses import dataclass
from types.settings import Settings
from typing import Any, Optional, Type, TypeVar

from sqlalchemy.orm.query import Query

T = TypeVar("T")
@dataclass
class SQLMixin:
    @classmethod
    @property
    def __tablename__(cls) -> str:
        return cls.__name__.lower()

    __sa_dataclass_metadata_key__ = "sa"

    @classmethod
    def query(cls: Type[T]) -> Query[T]:
        return Settings.session.query(cls)

    @classmethod
    def by_id(cls: Type[T], id: Any) -> Optional[T]:
        return Settings.session.query(cls).get(id)

    def save(self):
        Settings.session.add(self)
        Settings.session.commit()
    
    def reset(self):
        Settings.session.refresh(self)
    
    def delete(self):
        Settings.session.delete(self)
        Settings.session.commit()
