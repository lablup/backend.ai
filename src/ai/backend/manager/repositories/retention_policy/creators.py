from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import timedelta
from typing import override

from ai.backend.common.data.retention.types import RetentionCategory
from ai.backend.manager.errors.repository import UniqueConstraintViolationError
from ai.backend.manager.errors.retention import RetentionPolicyConflict
from ai.backend.manager.models.retention.row import RetentionPolicyRow
from ai.backend.manager.repositories.base.creator import CreatorSpec
from ai.backend.manager.repositories.base.types import IntegrityErrorCheck


@dataclass
class RetentionPolicyCreatorSpec(CreatorSpec[RetentionPolicyRow]):
    category: RetentionCategory
    retention_period: timedelta
    enabled: bool

    @property
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
        row = RetentionPolicyRow()
        row.category = self.category
        row.retention_period = self.retention_period
        row.enabled = self.enabled
        return row
