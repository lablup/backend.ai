from __future__ import annotations

import enum
from typing import Any, MutableMapping, TypedDict

__all__ = (
    "Sentinel",
    "Undefined",
    "sentinel",
    "undefined",
)


class Sentinel(enum.Enum):
    """
    A special type to represent a special value to indicate closing/shutdown of queues.
    """

    token = 0


class Undefined(enum.Enum):
    """
    A special type to represent an undefined value.
    """

    token = 0


sentinel = Sentinel.token
undefined = Undefined.token


def set_if_set(
    target_dict: MutableMapping[str, Any],
    key: str,
    value: Any | Undefined,
) -> None:
    if value is not undefined:
        target_dict[key] = value


class GraphQLInputVars(TypedDict):
    name: str
    input: MutableMapping[str, Any]
