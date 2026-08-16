from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.resource_policy import (
    USER_RESOURCE_POLICY_ENTITY_TYPE,
)
from ai.backend.common.data.entity.types import EntityType, ScopeRef
from ai.backend.common.data.entity.user import USER_SCOPE_TYPE
from ai.backend.manager.actions.v2.ops.base import OperationScopeOpsAction
from ai.backend.manager.data.resource.types import UserResourcePolicyData
from ai.backend.manager.models.resource_policy.row import UserResourcePolicyRow
from ai.backend.manager.models.scopes import OperationScope
from ai.backend.manager.repositories.user_resource_policy.searchers import (
    UserResourcePolicySearcher,
)
from ai.backend.manager.repositories.user_resource_policy.types import (
    UserResourcePolicyOperationScope,
)


@dataclass
class SearchUserResourcePoliciesAction(
    OperationScopeOpsAction[UserResourcePolicyRow, UserResourcePolicyData]
):
    """Read the policies in effect within the scopes the caller names."""

    scopes: Sequence[UserResourcePolicyOperationScope]
    searcher: UserResourcePolicySearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return USER_RESOURCE_POLICY_ENTITY_TYPE

    @override
    def scope_targets(self) -> Sequence[ScopeRef]:
        return tuple(
            ScopeRef(scope_type=USER_SCOPE_TYPE, scope_id=scope.user_id) for scope in self.scopes
        )

    @override
    def operation_scopes(self) -> Sequence[OperationScope]:
        return tuple(self.scopes)

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_user_resource_policies"

    @override
    def to_searcher(self) -> UserResourcePolicySearcher:
        return self.searcher
