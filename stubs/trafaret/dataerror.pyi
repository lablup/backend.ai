from typing import Any, Optional

from trafaret.base import Trafaret

class DataError(ValueError):
    def __init__(
        self,
        error: Optional[str] = None,
        name: Optional[str] = None,
        value: Any = ...,
        trafaret: Optional[Trafaret] = None,
    ): ...
    def as_dict(self, value=False): ...
    ...
