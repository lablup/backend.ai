from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ai.backend.manager.data.app_config_fragment.types import AppConfigFragmentData


@dataclass(frozen=True)
class AppConfigData:
    """Merged per-user view of one ``config_name``.

    The contributing ``fragments`` (rank low -> high) plus their deep-merged ``merged_config``.
    At least one fragment always contributes, so an empty ``merged_config`` means the
    fragments themselves were empty — not that none were found.
    """

    config_name: str
    fragments: list[AppConfigFragmentData]
    merged_config: dict[str, Any]
