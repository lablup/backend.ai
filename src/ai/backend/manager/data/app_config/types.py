from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AppConfigData:
    """Merged per-user view of one ``config_name``.

    ``config`` is every visible fragment deep-merged, not the fragments themselves — the
    fragment API answers which scope holds which value. An empty ``config`` therefore means
    either that nothing visible contributed or that everything that did was empty.
    """

    config_name: str
    config: dict[str, Any]
