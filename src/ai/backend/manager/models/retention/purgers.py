from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.identifier.retention_policy import RetentionPolicyID
from ai.backend.manager.data.retention.types import RetentionPolicyData
from ai.backend.manager.models.retention.row import RetentionPolicyRow
from ai.backend.manager.models.specs.purger import EntityPurger
from ai.backend.manager.models.specs.types import ConflictCheck


@dataclass
class RetentionPolicyPurger(EntityPurger[RetentionPolicyRow, RetentionPolicyData]):
    """Purger for deleting a retention policy."""

    policy_id: RetentionPolicyID

    @override
    def row_class(self) -> type[RetentionPolicyRow]:
        return RetentionPolicyRow

    @override
    def pk_value(self) -> RetentionPolicyID:
        return self.policy_id

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.policy_id

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: RetentionPolicyRow) -> RetentionPolicyData:
        return row.to_data()
