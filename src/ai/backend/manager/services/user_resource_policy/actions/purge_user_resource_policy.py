from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.resource_policy import (
    USER_RESOURCE_POLICY_ENTITY_TYPE,
    UserResourcePolicyUUID,
)
from ai.backend.common.data.entity.types import EntityID, EntityType
from ai.backend.manager.actions.v2.ops.base import PurgeEntityOpsAction
from ai.backend.manager.data.resource.types import UserResourcePolicyData
from ai.backend.manager.models.resource_policy.purgers import (
    UserResourcePolicyPurger,
)
from ai.backend.manager.models.resource_policy.row import UserResourcePolicyRow


@dataclass
class PurgeUserResourcePolicyAction(
    PurgeEntityOpsAction[UserResourcePolicyRow, UserResourcePolicyData]
):
    """Remove a user resource policy.

    Purge-shaped: the table carries no lifecycle column, so deleting one has
    always been the row leaving the table."""

    name: str
    policy_id: UserResourcePolicyUUID

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return USER_RESOURCE_POLICY_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_purge_user_resource_policy"

    @override
    def entity_id(self) -> EntityID:
        return self.to_purger().entity_id()

    @override
    def to_purger(self) -> UserResourcePolicyPurger:
        return UserResourcePolicyPurger(name=self.name, policy_id=self.policy_id)
