from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.retention_policy import RetentionPolicyID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import PartialBulkGetEntityOpsAction
from ai.backend.manager.data.retention.types import RetentionPolicyData
from ai.backend.manager.models.retention.queriers import BulkRetentionPolicyQuerier
from ai.backend.manager.models.retention.row import RetentionPolicyRow


@dataclass
class BulkGetRetentionPoliciesAction(
    PartialBulkGetEntityOpsAction[RetentionPolicyRow, RetentionPolicyData]
):
    """Read the retention policies the caller named, one permission check per policy."""

    ids: Sequence[RetentionPolicyID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_get_retention_policies"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(self.ids)

    @override
    def to_querier(self) -> BulkRetentionPolicyQuerier:
        return BulkRetentionPolicyQuerier()

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(self, ids=[entity_id for entity_id in self.ids if entity_id in allowed])
