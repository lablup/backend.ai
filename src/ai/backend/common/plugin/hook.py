from __future__ import annotations

import enum
from abc import ABCMeta, abstractmethod
from collections.abc import Sequence
from typing import Any, Final, Protocol

import attrs

from . import AbstractPlugin

__all__ = (
    "ALL_COMPLETED",
    "ERROR",
    "FIRST_COMPLETED",
    "PASSED",
    "REJECTED",
    "HookHandler",
    "HookPlugin",
    "HookResult",
    "HookResults",
    "HookReturnTiming",
    "Reject",
)


class HookHandler(Protocol):
    """
    Returns None when the handler does not handle the event, and a non-None result when it does.
    Raises :class:`Reject` to reject the event.
    """

    async def __call__(self, *args: Any) -> Any:
        # NOTE: Until https://github.com/python/mypy/issues/5876 is resolved,
        #       the get_handlers() in the HookPlugin subclasses should be marked
        #       with "type: ignore" comments.
        ...


class HookPlugin(AbstractPlugin, metaclass=ABCMeta):
    """
    The abstract interface for hook plugins.
    """

    @abstractmethod
    def get_handlers(self) -> Sequence[tuple[str, HookHandler]]:
        """
        Returns a sequence of pairs of the event name
        and its corresponding handler function.
        """
        pass


class Reject(Exception):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class HookResults(enum.Enum):
    PASSED = 0
    REJECTED = 1
    ERROR = 2


class HookReturnTiming(enum.Enum):
    ALL_COMPLETED = 0
    FIRST_COMPLETED = 1


PASSED: Final = HookResults.PASSED
REJECTED: Final = HookResults.REJECTED
ERROR: Final = HookResults.ERROR
ALL_COMPLETED: Final = HookReturnTiming.ALL_COMPLETED
FIRST_COMPLETED: Final = HookReturnTiming.FIRST_COMPLETED


@attrs.define(auto_attribs=True, slots=True)
class HookResult:
    status: HookResults
    src_plugin: str | Sequence[str] | None = None
    reason: str | None = None
    result: Any | None = None
