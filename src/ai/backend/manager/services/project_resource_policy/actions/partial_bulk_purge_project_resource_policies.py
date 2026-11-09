from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.resource_policy import ProjectResourcePolicyUUID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import PartialBulkPurgeEntityOpsAction
from ai.backend.manager.data.resource.types import ProjectResourcePolicyData
from ai.backend.manager.models.resource_policy.purgers import ProjectResourcePolicyPurger
from ai.backend.manager.models.resource_policy.row import ProjectResourcePolicyRow


@dataclass(frozen=True)
class PartialBulkPurgeProjectResourcePoliciesAction(
    PartialBulkPurgeEntityOpsAction[ProjectResourcePolicyRow, ProjectResourcePolicyData]
):
    """Remove the named project resource policies, answering for each one."""

    ids: Sequence[ProjectResourcePolicyUUID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "partial_bulk_purge_project_resource_policies"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(self.ids)

    @override
    def to_purgers(self) -> Mapping[EntityIdentifier, ProjectResourcePolicyPurger]:
        return {
            policy_id: ProjectResourcePolicyPurger(policy_id=policy_id) for policy_id in self.ids
        }

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(self, ids=[policy_id for policy_id in self.ids if policy_id in allowed])
