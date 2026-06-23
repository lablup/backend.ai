from __future__ import annotations

import enum
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from ai.backend.common.identifier.app_config_fragment import AppConfigFragmentID


class AppConfigScopeType(enum.StrEnum):
    """Scope at which an app config fragment is written (BEP-1052)."""

    PUBLIC = "public"
    DOMAIN = "domain"
    USER = "user"


@dataclass(frozen=True)
class AppConfigFragmentData:
    """Domain data for one app config fragment — a single scoped JSON document."""

    id: AppConfigFragmentID
    config_name: str
    scope_type: AppConfigScopeType
    scope_id: str
    rank: int
    config: dict[str, Any]
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class AppConfigFragmentSearchResult:
    """Search result with total count for app config fragments."""

    items: list[AppConfigFragmentData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
