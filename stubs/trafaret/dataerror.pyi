from typing import Any

from trafaret.base import Trafaret

class DataError(ValueError):
    error: str | dict[str, Any] | None
    name: str | None
    value: Any
    trafaret: Trafaret | None
    code: str | None

    def __init__(
        self,
        error: str | dict[str, Any] | None = None,
        name: str | None = None,
        value: Any = ...,
        trafaret: Trafaret | None = None,
    ): ...
    def as_dict(self, value: bool = False) -> str | dict[str, Any]: ...
    ...
