from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from ai.backend.common.data.retention.types import RetentionCategory
from ai.backend.common.identifier.retention_policy import RetentionPolicyID

__all__ = (
    "RetentionCategory",
    "RetentionPolicyData",
    "RetentionPolicySearchResult",
    "RetentionPurgeResult",
)


@dataclass(frozen=True)
class RetentionPolicyData:
    """A retention policy row: per-category admin-tunable cleanup settings."""

    id: RetentionPolicyID
    category: RetentionCategory
    retention_period: timedelta
    enabled: bool
    last_swept_at: datetime | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class RetentionPolicySearchResult:
    """Search result with total count for retention policies."""

    items: list[RetentionPolicyData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool


@dataclass(frozen=True)
class RetentionPurgeResult:
    """Outcome of purging one category's older-than-threshold rows.

    ``deleted_count`` is the total rows removed across the category's tables,
    letting the sweep account the result against its per-tick budget.
    """

    category: RetentionCategory
    deleted_count: int
