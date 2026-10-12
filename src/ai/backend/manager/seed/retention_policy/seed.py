from __future__ import annotations

from collections.abc import Sequence
from datetime import timedelta
from typing import override

from pydantic import Field

from ai.backend.common.data.entity.retention_policy import RetentionPolicyID
from ai.backend.common.data.retention.types import RetentionCategory
from ai.backend.manager.models.retention.upserters import RetentionPolicyUpserter
from ai.backend.manager.repositories.ops.v2.seed.types import SeedWrite
from ai.backend.manager.seed.base import SeedItem, SeedItems, SeedRejection


class RetentionPolicySeed(SeedItem):
    """One ``retention_policies`` row, keyed by its id. The period is in days, as the API
    takes it."""

    id: RetentionPolicyID
    category: RetentionCategory
    retention_period_days: int = Field(ge=1, le=timedelta.max.days)
    enabled: bool

    @override
    def key(self) -> str:
        return str(self.id)

    @override
    def write(self) -> SeedWrite:
        return SeedWrite(
            upserter=RetentionPolicyUpserter(
                id=self.id,
                category=self.category,
                retention_period=timedelta(days=self.retention_period_days),
                enabled=self.enabled,
            ),
            field_upserters=[],
            field_purgers=[],
        )

    @override
    @classmethod
    def reject(cls, files: Sequence[SeedItems[RetentionPolicySeed]]) -> list[SeedRejection]:
        return []
