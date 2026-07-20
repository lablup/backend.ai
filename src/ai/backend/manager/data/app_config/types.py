from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ai.backend.manager.data.app_config_fragment.types import AppConfigFragmentData


@dataclass(frozen=True)
class AppConfigData:
    """Merged per-user view of one ``config_name``.

    The ordered contributing ``fragments`` (rank low -> high) plus their deep-merged
    ``merged_config``. At least one fragment always contributes — a ``config_name`` nothing
    is visible for never reaches this type, it is an ``AppConfigFragmentNotFound``. An empty
    ``merged_config`` therefore means fragments merged to ``{}``, not that none were found.
    """

    config_name: str
    fragments: list[AppConfigFragmentData]
    merged_config: dict[str, Any]
