from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, override
from uuid import UUID

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.retention_policy import RetentionPolicyID
from ai.backend.common.data.retention.types import RetentionCategory
from ai.backend.manager.data.retention.types import RetentionPolicyData
from ai.backend.manager.models.retention.row import RetentionPolicyRow
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.updater import DataUpdater
from ai.backend.manager.types import OptionalState


@dataclass
class RetentionPolicyUpdater(DataUpdater[RetentionPolicyRow, RetentionPolicyData]):
    policy_id: RetentionPolicyID
    category: OptionalState[RetentionCategory] = field(
        default_factory=OptionalState[RetentionCategory].nop
    )
    retention_period: OptionalState[timedelta] = field(default_factory=OptionalState[timedelta].nop)
    enabled: OptionalState[bool] = field(default_factory=OptionalState[bool].nop)

    @property
    @override
    def row_class(self) -> type[RetentionPolicyRow]:
        return RetentionPolicyRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return RetentionPolicyRow.id

    @override
    def target_id_value(self) -> UUID:
        return self.policy_id

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.category.update_dict(to_update, "category")
        self.retention_period.update_dict(to_update, "retention_period")
        self.enabled.update_dict(to_update, "enabled")
        return to_update

    @override
    def to_data(self, row: RetentionPolicyRow) -> RetentionPolicyData:
        return row.to_data()


@dataclass
class LastSweptAtUpdater(DataUpdater[RetentionPolicyRow, RetentionPolicyData]):
    """Stamps a policy's ``last_swept_at`` after its category is swept."""

    policy_id: RetentionPolicyID
    last_swept_at: datetime

    @property
    @override
    def row_class(self) -> type[RetentionPolicyRow]:
        return RetentionPolicyRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return RetentionPolicyRow.id

    @override
    def target_id_value(self) -> UUID:
        return self.policy_id

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_values(self) -> dict[str, Any]:
        return {"last_swept_at": self.last_swept_at}

    @override
    def to_data(self, row: RetentionPolicyRow) -> RetentionPolicyData:
        return row.to_data()
