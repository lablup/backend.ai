from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import UpdatePartialBulkOpsAction
from ai.backend.manager.data.resource.types import ProjectResourcePolicyData
from ai.backend.manager.models.resource_policy.row import ProjectResourcePolicyRow
from ai.backend.manager.models.resource_policy.updaters import ProjectResourcePolicyUpdater


@dataclass(frozen=True)
class PartialBulkUpdateProjectResourcePoliciesAction(
    UpdatePartialBulkOpsAction[ProjectResourcePolicyRow, ProjectResourcePolicyData]
):
    """Retune the named project resource policies, answering for each one."""

    updaters: Sequence[ProjectResourcePolicyUpdater]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "partial_bulk_update_project_resource_policies"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(updater.policy_id for updater in self.updaters)

    @override
    def to_updaters(self) -> Mapping[EntityIdentifier, ProjectResourcePolicyUpdater]:
        return {updater.policy_id: updater for updater in self.updaters}

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(
            self, updaters=[updater for updater in self.updaters if updater.policy_id in allowed]
        )
