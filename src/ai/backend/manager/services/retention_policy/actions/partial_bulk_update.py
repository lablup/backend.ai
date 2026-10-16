from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import UpdatePartialBulkOpsAction
from ai.backend.manager.data.retention.types import RetentionPolicyData
from ai.backend.manager.models.retention.row import RetentionPolicyRow
from ai.backend.manager.models.retention.updaters import RetentionPolicyUpdater


@dataclass(frozen=True)
class PartialBulkUpdateRetentionPoliciesAction(
    UpdatePartialBulkOpsAction[RetentionPolicyRow, RetentionPolicyData]
):
    """Retune the named categories' cleanup settings, answering for each one."""

    updaters: Sequence[RetentionPolicyUpdater]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "partial_bulk_update_retention_policies"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(updater.policy_id for updater in self.updaters)

    @override
    def to_updaters(self) -> Mapping[EntityIdentifier, RetentionPolicyUpdater]:
        return {updater.policy_id: updater for updater in self.updaters}

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(
            self, updaters=[updater for updater in self.updaters if updater.policy_id in allowed]
        )
