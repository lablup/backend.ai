from __future__ import annotations

import enum
from dataclasses import dataclass
from datetime import datetime

from ai.backend.common.identifier.app_config_allow_list import AppConfigAllowListID


class AppConfigScopeType(enum.StrEnum):
    """Scope at which an app config fragment may be written (BEP-1052)."""

    PUBLIC = "public"
    DOMAIN = "domain"
    USER = "user"


@dataclass(frozen=True)
class AppConfigAllowListData:
    """Domain data for one app config allow-list entry — a per-``(config_name, scope_type)`` write gate."""

    id: AppConfigAllowListID
    config_name: str
    scope_type: AppConfigScopeType
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class AppConfigAllowListSearchResult:
    """Search result with total count for app config allow-list entries."""

    items: list[AppConfigAllowListData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
