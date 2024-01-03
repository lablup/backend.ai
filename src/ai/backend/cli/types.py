from __future__ import annotations

import enum
from typing import Dict

import attr

__all__ = (
    "Undefined",
    "undefined",
)


@attr.define(slots=True)
class CliContextInfo:
    info: Dict = attr.field()


class ExitCode(enum.IntEnum):
    OK = 0
    FAILURE = 1  # generic failure
    INVALID_USAGE = 2  # wraps Click's UsageError
    OPERATION_TIMEOUT = 3  # timeout during operation
    INVALID_ARGUMENT = 4  # invalid argument while it's not UsageError


class Undefined(enum.Enum):
    """
    A special type to represent an undefined value.
    """

    TOKEN = 0

    def __bool__(self) -> bool:
        # It should be evaluated as False when used as a boolean expr.
        return False


undefined = Undefined.TOKEN
