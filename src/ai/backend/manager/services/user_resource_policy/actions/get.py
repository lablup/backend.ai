from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.resource_policy import UserResourcePolicyUUID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import GetSingleEntityOpsAction
from ai.backend.manager.data.resource.types import UserResourcePolicyData
from ai.backend.manager.models.resource_policy.queriers import UserResourcePolicyQuerier
from ai.backend.manager.models.resource_policy.row import UserResourcePolicyRow


@dataclass(frozen=True)
class GetUserResourcePolicyAction(
    GetSingleEntityOpsAction[UserResourcePolicyRow, UserResourcePolicyData]
):
    """Read one user resource policy by its id."""

    policy_id: UserResourcePolicyUUID

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.policy_id

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_user_resource_policy"

    @override
    def to_querier(self) -> UserResourcePolicyQuerier:
        return UserResourcePolicyQuerier(uuid=self.policy_id)
