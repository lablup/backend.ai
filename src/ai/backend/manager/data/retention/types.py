from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import override

from ai.backend.common.data.entity.types import EntityData
from ai.backend.common.data.retention.types import RetentionCategory
from ai.backend.common.identifier.entity import EntityID
from ai.backend.common.identifier.retention_policy import RetentionPolicyID

__all__ = (
    "RetentionCategory",
    "RetentionPolicyData",
    "RetentionPurgeResult",
)


@dataclass(frozen=True)
class RetentionPolicyData(EntityData):
    """A retention policy row: per-category admin-tunable cleanup settings."""

    id: RetentionPolicyID
    category: RetentionCategory
    retention_period: timedelta
    enabled: bool
    last_swept_at: datetime | None
    created_at: datetime
    updated_at: datetime

    @override
    def entity_id(self) -> EntityID:
        return self.id


@dataclass(frozen=True)
class RetentionPurgeResult:
    """Outcome of purging one category's older-than-threshold rows.

    ``deleted_count`` is the total rows removed across the category's tables,
    letting the sweep account the result against its per-tick budget.
    """

    category: RetentionCategory
    deleted_count: int
