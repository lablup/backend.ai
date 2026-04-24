from __future__ import annotations

import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from ai.backend.manager.data.app_config_fragment.types import AppConfigFragmentData


@dataclass(frozen=True)
class AppConfigData:
    """Service-layer return type for the merged AppConfig view (BEP-1052 §5).

    `fragments` are ordered low → high merge priority (matching the
    policy's `scope_sources`). `config` is the deep-merged result,
    projected to `None` when every contributing fragment is empty.
    """

    user_id: uuid.UUID
    name: str
    fragments: Sequence[AppConfigFragmentData]
    config: Mapping[str, Any] | None


@dataclass(frozen=True)
class AppConfigSearchResult:
    """Result from searching merged `AppConfig` views."""

    items: list[AppConfigData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
