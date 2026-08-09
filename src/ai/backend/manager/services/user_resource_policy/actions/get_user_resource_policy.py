from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.resource_policy import (
    USER_RESOURCE_POLICY_ENTITY_TYPE,
)
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import GetGlobalOpsAction
from ai.backend.manager.data.resource.types import UserResourcePolicyData
from ai.backend.manager.models.resource_policy.row import UserResourcePolicyRow
from ai.backend.manager.repositories.user_resource_policy.queriers import (
    UserResourcePolicyQuerier,
)


@dataclass
class GetUserResourcePolicyAction(
    GetGlobalOpsAction[UserResourcePolicyRow, UserResourcePolicyData]
):
    """Read one user resource policy by name."""

    name: str

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return USER_RESOURCE_POLICY_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "admin_get_user_resource_policy"

    @override
    def to_querier(self) -> UserResourcePolicyQuerier:
        return UserResourcePolicyQuerier(name=self.name)
