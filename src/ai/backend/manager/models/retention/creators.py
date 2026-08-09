from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import timedelta
from typing import override

from ai.backend.common.data.retention.types import RetentionCategory
from ai.backend.manager.data.retention.types import RetentionPolicyData
from ai.backend.manager.errors.repository import UniqueConstraintViolationError
from ai.backend.manager.errors.retention import RetentionPolicyConflict
from ai.backend.manager.models.retention.row import RetentionPolicyRow
from ai.backend.manager.models.specs.creator import GlobalEntityCreator
from ai.backend.manager.models.specs.types import IntegrityErrorCheck


@dataclass
class RetentionPolicyCreator(GlobalEntityCreator[RetentionPolicyRow, RetentionPolicyData]):
    """Creator for a retention policy — one row per category, admin-managed."""

    category: RetentionCategory
    retention_period: timedelta
    enabled: bool

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return (
            IntegrityErrorCheck(
                violation_type=UniqueConstraintViolationError,
                error=RetentionPolicyConflict(
                    f"A retention policy for category '{self.category}' already exists."
                ),
            ),
        )

    @override
    def build_row(self) -> RetentionPolicyRow:
        return RetentionPolicyRow(
            category=self.category,
            retention_period=self.retention_period,
            enabled=self.enabled,
        )

    @override
    def to_data(self, row: RetentionPolicyRow) -> RetentionPolicyData:
        return row.to_data()
