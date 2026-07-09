from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ai.backend.manager.data.app_config_fragment.types import AppConfigFragmentData


@dataclass(frozen=True)
class AppConfigData:
    """Merged per-user view of one ``config_name``.

    The ordered contributing ``fragments`` (rank low -> high) plus their deep-merged
    ``merged_config``. ``merged_config`` is ``None`` when no fragment contributes (the config
    name is defined but unconfigured for this scope) — distinct from a fragment that merges
    to an empty ``{}``.
    """

    config_name: str
    fragments: list[AppConfigFragmentData]
    merged_config: dict[str, Any] | None
