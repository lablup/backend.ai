from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ai.backend.manager.api.utils import Undefined


def drop_undefined(d: dict[Any, Any]) -> dict[Any, Any]:
    newd: dict[Any, Any] = {}
    for k, v in d.items():
        if isinstance(v, (Mapping, dict)):
            newval = drop_undefined(dict(v))
            if len(newval.keys()) > 0:  # exclude empty dict always
                newd[k] = newval
        elif not isinstance(v, Undefined):
            newd[k] = v
    return newd
