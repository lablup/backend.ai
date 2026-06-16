from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.common.identifier.app_config_fragment import AppConfigFragmentID

__all__ = (
    "AppConfigFragmentData",
    "AppConfigFragmentKey",
    "AppConfigFragmentSearchResult",
    "AppConfigScopeType",
)


@dataclass(frozen=True, slots=True)
class AppConfigFragmentKey:
    """Natural-key identifier for a single `app_config_fragments` row."""

    scope_type: AppConfigScopeType
    scope_id: str
    name: str


@dataclass(frozen=True)
class AppConfigFragmentData:
    id: AppConfigFragmentID
    scope_type: AppConfigScopeType
    scope_id: str
    name: str
    rank: int
    config: Mapping[str, Any] | None
    created_at: datetime
    updated_at: datetime

    @property
    def key(self) -> AppConfigFragmentKey:
        return AppConfigFragmentKey(
            scope_type=self.scope_type,
            scope_id=self.scope_id,
            name=self.name,
        )


@dataclass(frozen=True)
class AppConfigFragmentSearchResult:
    """Result from searching raw `app_config_fragments` rows."""

    items: list[AppConfigFragmentData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
