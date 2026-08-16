"""DataQuerier implementations for the retention policy repository."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.retention_policy import RetentionPolicyID
from ai.backend.manager.data.retention.types import RetentionPolicyData
from ai.backend.manager.models.retention.row import RetentionPolicyRow
from ai.backend.manager.models.specs.querier import DataQuerier


@dataclass
class RetentionPolicyQuerier(DataQuerier[RetentionPolicyRow, RetentionPolicyData]):
    policy_id: RetentionPolicyID

    @override
    def row_class(self) -> type[RetentionPolicyRow]:
        return RetentionPolicyRow

    @override
    def pk_value(self) -> RetentionPolicyID:
        return self.policy_id

    @override
    def to_data(self, row: RetentionPolicyRow) -> RetentionPolicyData:
        return row.to_data()
