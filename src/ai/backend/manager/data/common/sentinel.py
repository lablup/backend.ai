from __future__ import annotations

from collections.abc import MutableMapping
from typing import Any


class Singleton(type):
    _instances: MutableMapping[Any, Any] = {}

    def __call__(cls, *args: Any, **kwargs: Any) -> Any:
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class Undefined(metaclass=Singleton):
    pass


undefined = Undefined()
