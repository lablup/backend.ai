from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.resource_policy import UserResourcePolicyUUID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import PartialBulkPurgeEntityOpsAction
from ai.backend.manager.data.resource.types import UserResourcePolicyData
from ai.backend.manager.models.resource_policy.purgers import UserResourcePolicyPurger
from ai.backend.manager.models.resource_policy.row import UserResourcePolicyRow


@dataclass(frozen=True)
class PartialBulkPurgeUserResourcePoliciesAction(
    PartialBulkPurgeEntityOpsAction[UserResourcePolicyRow, UserResourcePolicyData]
):
    """Remove the named user resource policies, answering for each one."""

    ids: Sequence[UserResourcePolicyUUID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "partial_bulk_purge_user_resource_policies"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(self.ids)

    @override
    def to_purgers(self) -> Mapping[EntityIdentifier, UserResourcePolicyPurger]:
        return {policy_id: UserResourcePolicyPurger(policy_id=policy_id) for policy_id in self.ids}

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(self, ids=[policy_id for policy_id in self.ids if policy_id in allowed])
