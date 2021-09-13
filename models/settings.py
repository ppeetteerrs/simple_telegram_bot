from __future__ import annotations

from datetime import datetime
from typing import ClassVar, Optional

from sqlalchemy import create_engine
from sqlalchemy.engine.base import Engine
from sqlalchemy.orm import registry, sessionmaker
from sqlalchemy.orm.session import Session
from telebot import TeleBot

mapper_registry = registry()
sql_map = mapper_registry.mapped


class Settings:
    _token: ClassVar[Optional[str]] = None
    _db_name: ClassVar[Optional[str]] = None
    _bot: ClassVar[Optional[TeleBot]] = None
    _engine: ClassVar[Optional[Engine]] = None
    _session: ClassVar[Optional[Session]] = None
    start_time: ClassVar[datetime] = datetime.now()

    @classmethod
    def start(cls, token: str, db_name: str) -> None:
        """
        Starts TeleBot and SQLite connection

        :param token: Telegram API key
        :param db_name: SQLite database filename
        """

        cls._token = token
        cls._db_name = db_name
        cls._bot = TeleBot(token, parse_mode="MARKDOWN")
        engine = create_engine(f"sqlite:///{db_name}", connect_args={"check_same_thread": False})
        cls._engine = engine
        cls._session = sessionmaker(engine)()
        mapper_registry.metadata.create_all(engine)

    @classmethod
    @property
    def token(cls) -> str:
        """Telegram API key"""

        if cls._token is not None:
            return cls._token
        else:
            raise ValueError("Token is not set.")

    @classmethod
    @property
    def db_name(cls) -> str:
        """SQLite database filename"""

        if cls._db_name is not None:
            return cls._db_name
        else:
            raise ValueError("DB name is not set.")

    @classmethod
    @property
    def bot(cls) -> TeleBot:
        """Telebot instance"""

        if cls._bot is not None:
            return cls._bot
        else:
            raise ValueError("Bot is not set.")

    @classmethod
    @property
    def engine(cls) -> Engine:
        """SQLAlchemy engine"""

        if cls._engine is not None:
            return cls._engine
        else:
            raise ValueError("Engine is not set.")

    @classmethod
    @property
    def session(cls) -> Session:
        """SQLAlchemy session"""

        if cls._session is not None:
            return cls._session
        else:
            raise ValueError("Session is not set.")
