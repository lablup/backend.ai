from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.retention_policy import RetentionPolicyID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import PartialBulkPurgeEntityOpsAction
from ai.backend.manager.data.retention.types import RetentionPolicyData
from ai.backend.manager.models.retention.purgers import RetentionPolicyPurger
from ai.backend.manager.models.retention.row import RetentionPolicyRow


@dataclass(frozen=True)
class PartialBulkPurgeRetentionPoliciesAction(
    PartialBulkPurgeEntityOpsAction[RetentionPolicyRow, RetentionPolicyData]
):
    """Remove the named retention policy rows from the catalog, answering for each one."""

    ids: Sequence[RetentionPolicyID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "partial_bulk_purge_retention_policies"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(self.ids)

    @override
    def to_purgers(self) -> Mapping[EntityIdentifier, RetentionPolicyPurger]:
        return {policy_id: RetentionPolicyPurger(policy_id=policy_id) for policy_id in self.ids}

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(self, ids=[policy_id for policy_id in self.ids if policy_id in allowed])
