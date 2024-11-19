from typing import Any, Optional

from trafaret.base import Trafaret

class DataError(ValueError):
    error: Optional[str | dict[str, Any]]
    name: Optional[str]
    value: Any
    trafaret: Optional[Trafaret]
    code: Optional[str]

    def __init__(
        self,
        error: Optional[str | dict[str, Any]] = None,
        name: Optional[str] = None,
        value: Any = ...,
        trafaret: Optional[Trafaret] = None,
    ): ...
    def as_dict(self, value: bool = False): ...
    ...
