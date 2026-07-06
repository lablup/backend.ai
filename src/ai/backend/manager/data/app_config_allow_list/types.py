from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.common.identifier.app_config_allow_list import AppConfigAllowListID


@dataclass(frozen=True)
class AppConfigAllowListData:
    """Domain data for one app config allow-list entry — a per-``(config_name, scope_type)`` write gate.

    ``rank`` is the merge priority applied to every fragment written under the entry
    (low → high; higher wins).
    """

    id: AppConfigAllowListID
    config_name: str
    scope_type: AppConfigScopeType
    rank: int
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class AppConfigAllowListSearchResult:
    """Search result with total count for app config allow-list entries."""

    items: list[AppConfigAllowListData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
