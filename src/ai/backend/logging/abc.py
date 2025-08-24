from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import Self

from .config_pydantic import LoggingConfig


class AbstractLogger(metaclass=ABCMeta):
    def __init__(self, config: LoggingConfig) -> None: ...

    @abstractmethod
    def __enter__(self) -> Self:
        raise NotImplementedError

    @abstractmethod
    def __exit__(self, *exc_info_args) -> bool | None:
        raise NotImplementedError
