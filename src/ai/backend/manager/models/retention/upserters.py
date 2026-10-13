from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import timedelta
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.entity.retention_policy import RetentionPolicyID
from ai.backend.common.data.retention.types import RetentionCategory
from ai.backend.manager.data.retention.types import RetentionPolicyData
from ai.backend.manager.models.retention.row import RetentionPolicyRow
from ai.backend.manager.models.retention.searchable_fields import (
    RetentionPolicySearchableFields,
)
from ai.backend.manager.models.specs.created_in import CreatedInGlobal
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.upserter import EntityUpserter

__all__ = ("RetentionPolicyUpserter",)


@dataclass
class RetentionPolicyUpserter(
    CreatedInGlobal[RetentionPolicyRow], EntityUpserter[RetentionPolicyRow, RetentionPolicyData]
):
    """Write a retention policy under its stated id.

    Conflict key: id. ``last_swept_at`` is left as it is.
    """

    id: RetentionPolicyID
    category: RetentionCategory
    retention_period: timedelta
    enabled: bool

    @override
    def entity_id(self, row: RetentionPolicyRow) -> RetentionPolicyID:
        return RetentionPolicyID(row.id)

    @override
    def row_class(self) -> type[RetentionPolicyRow]:
        return RetentionPolicyRow

    @override
    def index_elements(self) -> list[str]:
        return ["id"]

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_insert_values(self) -> dict[str, Any]:
        return {"id": self.id, **self._values()}

    @override
    def build_update_values(self) -> dict[str, Any]:
        """``updated_at`` is set here: ``ON CONFLICT DO UPDATE`` bypasses the ORM's
        ``onupdate``."""
        return {**self._values(), "updated_at": sa.func.now()}

    def _values(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "retention_period": self.retention_period,
            "enabled": self.enabled,
        }

    @override
    def to_data(self, row: RetentionPolicyRow) -> RetentionPolicyData:
        return RetentionPolicySearchableFields.own.to_data(row)
