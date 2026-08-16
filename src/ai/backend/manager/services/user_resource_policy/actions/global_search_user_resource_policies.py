from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.resource_policy import (
    USER_RESOURCE_POLICY_ENTITY_TYPE,
)
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import SearchGlobalOpsAction
from ai.backend.manager.data.resource.types import UserResourcePolicyData
from ai.backend.manager.models.resource_policy.row import UserResourcePolicyRow
from ai.backend.manager.repositories.user_resource_policy.searchers import (
    UserResourcePolicySearcher,
)


@dataclass
class GlobalSearchUserResourcePoliciesAction(
    SearchGlobalOpsAction[UserResourcePolicyRow, UserResourcePolicyData]
):
    """Page through the user resource policy catalog."""

    searcher: UserResourcePolicySearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return USER_RESOURCE_POLICY_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_search_user_resource_policies"

    @override
    def to_searcher(self) -> UserResourcePolicySearcher:
        return self.searcher
