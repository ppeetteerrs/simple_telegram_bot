import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Optional


@dataclass
class DataClass:
    """
    A dataclass with built-in IO operations.
        key: returns a unique key to be used as filename
        dir: data directory to save file to
        save: self-explanatory
        load: self-explanatory
    """

    @property
    def key(self) -> Any:
        raise NotImplementedError("key method not implemented.")

    @classmethod
    def dir(cls) -> str:
        raise NotImplementedError("dir method not implemented.")

    def save(self) -> None:
        parent = Path("data") / self.dir()
        filename = f"{str(self.key).replace('.json', '')}.json"
        parent.mkdir(parents=True, exist_ok=True)
        path = (parent / filename).resolve()

        json.dump(asdict(self), open(path, "w"))

    @classmethod
    def load(cls, key: Any) -> Optional["DataClass"]:
        try:
            filename = f"{str(key).replace('.json', '')}.json"

            return cls(
                **json.load(
                    open((Path("data") / cls.dir() / filename).resolve(), "r")
                )
            )

        except Exception:
            return None


@dataclass
class User(DataClass):
    """User metadata dataclass"""

    id_: int
    username: str
    email: str = None

    @property
    def key(self) -> int:
        return self.id_

    @classmethod
    def dir(cls) -> str:
        return "users"
