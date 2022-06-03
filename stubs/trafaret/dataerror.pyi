from typing import Any
from trafaret.base import Trafaret

class DataError(ValueError):
    def __init__(self,
                 error: str = None,
                 name: str = None,
                 value: Any = ...,
                 trafaret: Trafaret = None): ...
    def as_dict(self, value=False): ...
    ...
