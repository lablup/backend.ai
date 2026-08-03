from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AppConfigData:
    """Merged per-user view of one ``config_name``.

    Only the merge is carried, not the fragments behind it — the fragment API answers which
    scope holds which value. An empty ``merged_config`` therefore means either that nothing
    visible contributed or that everything that did was empty.
    """

    config_name: str
    merged_config: dict[str, Any]
