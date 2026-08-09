from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.resource_policy import (
    USER_RESOURCE_POLICY_ENTITY_TYPE,
)
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import CreateGlobalOpsAction
from ai.backend.manager.data.resource.types import UserResourcePolicyData
from ai.backend.manager.models.resource_policy.creators import (
    UserResourcePolicyCreator,
)
from ai.backend.manager.models.resource_policy.row import UserResourcePolicyRow


@dataclass
class CreateUserResourcePolicyAction(
    CreateGlobalOpsAction[UserResourcePolicyRow, UserResourcePolicyData]
):
    """Register a user resource policy."""

    creator: UserResourcePolicyCreator

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return USER_RESOURCE_POLICY_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "admin_create_user_resource_policy"

    @override
    def to_creator(self) -> UserResourcePolicyCreator:
        return self.creator
