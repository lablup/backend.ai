"""Write specs for a retention policy."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import override

from bai_scenario.seeds.seeder import Naming, SeedRow

from ai.backend.common.data.retention.types import RetentionCategory
from ai.backend.manager.data.retention.types import RetentionPolicyData
from ai.backend.manager.models.retention.creators import RetentionPolicyCreator


@dataclass(frozen=True)
class SeedRetentionPolicy(SeedRow[RetentionPolicyData]):
    """The one policy of a category. Its name is the category, which the manager fixes."""

    category: RetentionCategory = RetentionCategory.LOGS
    retention_days: int = 30
    enabled: bool = True

    @override
    def kind(self) -> str:
        return "보존 정책"

    @override
    def detail(self) -> str:
        parts = [f"{self.retention_days}일 보존"]
        if not self.enabled:
            parts.append("비활성")
        return ", ".join(parts)

    @override
    def name(self, naming: Naming) -> str:
        return self.category.value

    @override
    def seed(self, name: str) -> RetentionPolicyCreator:
        return RetentionPolicyCreator(
            category=self.category,
            retention_period=timedelta(days=self.retention_days),
            enabled=self.enabled,
        )
