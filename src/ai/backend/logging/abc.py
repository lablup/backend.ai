from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import Any, MutableMapping, Self

from .utils import _register_custom_loglevels


class AbstractLogger(metaclass=ABCMeta):
    def __init__(
        self,
        logging_config: MutableMapping[str, Any],
    ) -> None:
        _register_custom_loglevels()

    @abstractmethod
    def __enter__(self) -> Self:
        raise NotImplementedError

    @abstractmethod
    def __exit__(self, *exc_info_args) -> bool | None:
        raise NotImplementedError
