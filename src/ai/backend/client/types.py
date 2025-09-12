from __future__ import annotations

from collections.abc import MutableMapping
from typing import Any, Callable

from ai.backend.cli.types import Undefined, undefined


def set_if_set(
    target_dict: MutableMapping[str, Any],
    key: str,
    value: Any | Undefined,
    *,
    clean_func: Callable[[Any], Any] | None = None,
) -> None:
    if value is not undefined:
        if clean_func is not None:
            value = clean_func(value)
        target_dict[key] = value
