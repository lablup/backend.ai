from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.common.identifier.app_config import AppConfigScopeIdentifier
from ai.backend.common.identifier.app_config_fragment import AppConfigFragmentID


@dataclass(frozen=True)
class AppConfigFragmentData:
    """Domain data for one app config fragment — a single scoped JSON document."""

    id: AppConfigFragmentID
    config_name: str
    scope_type: AppConfigScopeType
    scope_id: AppConfigScopeIdentifier | None
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


@dataclass(frozen=True)
class AppConfigFragmentBulkItemError:
    """One failed item of a partial bulk mutation: the fragment it targeted and a reason.

    Every bulk item names its own fragment, so the id is what the caller can act on — a
    batch position would make them correlate the failure back by hand.
    """

    id: AppConfigFragmentID
    message: str


@dataclass(frozen=True)
class AppConfigFragmentBulkResult:
    """Partial-success result of a bulk mutation.

    ``succeeded`` are the fragments that were created/updated/purged; ``failed`` are the items
    whose write failed (e.g. no allow-list row, or a missing target), each with its batch
    ``index`` and a reason.
    """

    succeeded: list[AppConfigFragmentData]
    failed: list[AppConfigFragmentBulkItemError]
