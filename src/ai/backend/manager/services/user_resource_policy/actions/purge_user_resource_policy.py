from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.resource_policy import (
    USER_RESOURCE_POLICY_ENTITY_TYPE,
)
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import PurgeGlobalOpsAction
from ai.backend.manager.data.resource.types import UserResourcePolicyData
from ai.backend.manager.models.resource_policy.purgers import (
    UserResourcePolicyPurger,
)
from ai.backend.manager.models.resource_policy.row import UserResourcePolicyRow


@dataclass
class PurgeUserResourcePolicyAction(
    PurgeGlobalOpsAction[UserResourcePolicyRow, UserResourcePolicyData]
):
    """Remove a user resource policy.

    Purge-shaped: the table carries no lifecycle column, so deleting one has
    always been the row leaving the table."""

    name: str

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return USER_RESOURCE_POLICY_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "admin_purge_user_resource_policy"

    @override
    def to_purger(self) -> UserResourcePolicyPurger:
        return UserResourcePolicyPurger(name=self.name)
