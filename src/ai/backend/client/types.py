from __future__ import annotations

from collections.abc import Callable, MutableMapping
from typing import Any

from ai.backend.cli.types import Undefined, undefined
from ai.backend.common.types import Sentinel

__all__ = (
    "Sentinel",
    "sentinel",
)

# Re-export for backwards compatibility
sentinel = Sentinel.TOKEN


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
