from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.resource_policy import (
    USER_RESOURCE_POLICY_ENTITY_TYPE,
)
from ai.backend.common.data.entity.types import EntityType, ScopeRef
from ai.backend.common.data.entity.user import USER_ENTITY_TYPE, USER_SCOPE_TYPE, UserID
from ai.backend.manager.actions.v2.ops.base import OperationScopeOpsAction
from ai.backend.manager.data.resource.types import UserResourcePolicyData
from ai.backend.manager.models.resource_policy.row import UserResourcePolicyRow
from ai.backend.manager.models.resource_policy.scopes import UserResourcePolicyOperationScope
from ai.backend.manager.models.resource_policy.searchers import (
    UserResourcePolicySearcher,
)
from ai.backend.manager.models.scopes import OperationScope


@dataclass
class SearchUserResourcePoliciesAction(
    OperationScopeOpsAction[UserResourcePolicyRow, UserResourcePolicyData]
):
    """Page through the user resource policies that apply within a user scope.

    Which user that is, is the caller's business: the scope is an argument.
    """

    user_id: UserID
    searcher: UserResourcePolicySearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return USER_RESOURCE_POLICY_ENTITY_TYPE

    @override
    def scope_targets(self) -> Sequence[ScopeRef]:
        return (ScopeRef(scope_type=USER_SCOPE_TYPE, scope_id=self.user_id),)

    @override
    @classmethod
    def available_scope_types(cls) -> Sequence[EntityType]:
        return (USER_ENTITY_TYPE,)

    @override
    def operation_scopes(self) -> Sequence[OperationScope]:
        return (UserResourcePolicyOperationScope(user_id=self.user_id),)

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_user_resource_policies"

    @override
    def to_searcher(self) -> UserResourcePolicySearcher:
        return self.searcher
