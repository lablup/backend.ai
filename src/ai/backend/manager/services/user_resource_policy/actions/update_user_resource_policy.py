from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.resource_policy import (
    USER_RESOURCE_POLICY_ENTITY_TYPE,
)
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import UpdateGlobalOpsAction
from ai.backend.manager.data.resource.types import UserResourcePolicyData
from ai.backend.manager.models.resource_policy.row import UserResourcePolicyRow
from ai.backend.manager.models.resource_policy.updaters import (
    UserResourcePolicyUpdater,
)


@dataclass
class UpdateUserResourcePolicyAction(
    UpdateGlobalOpsAction[UserResourcePolicyRow, UserResourcePolicyData]
):
    """Retune one user resource policy; the name stays the key."""

    updater: UserResourcePolicyUpdater

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return USER_RESOURCE_POLICY_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "admin_update_user_resource_policy"

    @override
    def to_updater(self) -> UserResourcePolicyUpdater:
        return self.updater
