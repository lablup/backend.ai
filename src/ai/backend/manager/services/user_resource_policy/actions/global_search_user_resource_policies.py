from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.resource_policy import (
    UserResourcePolicyEntityType,
)
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import GlobalSearcherOpsAction
from ai.backend.manager.data.resource.types import UserResourcePolicyData
from ai.backend.manager.models.resource_policy.row import UserResourcePolicyRow


@dataclass(frozen=True)
class GlobalSearchUserResourcePoliciesAction(
    GlobalSearcherOpsAction[UserResourcePolicyRow, UserResourcePolicyData]
):
    """Page through the user resource policy catalog."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return UserResourcePolicyEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_search_user_resource_policies"
