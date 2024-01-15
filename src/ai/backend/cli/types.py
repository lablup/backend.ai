from __future__ import annotations

import enum
from pathlib import Path
from typing import Dict

import attr
from pydantic import BaseModel, Field

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


class MountType(enum.StrEnum):
    BIND = "bind"
    VOLUME = "volume"
    TMPFS = "tmpfs"
    CLUSTER = "cluster"


class MountPoint(BaseModel):
    type: MountType = Field(default=MountType.BIND)
    source: Path
    target: Path | None = Field(default=None)
    readonly: bool = Field(default=False)
