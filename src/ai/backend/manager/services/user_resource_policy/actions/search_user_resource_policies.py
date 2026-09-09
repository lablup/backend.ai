from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.resource_policy import (
    UserResourcePolicyEntityType,
)
from ai.backend.common.data.entity.types import EntityType, ScopeRef
from ai.backend.common.data.entity.user import USER_SCOPE_TYPE, UserID
from ai.backend.manager.actions.v2.ops.base import OperationScopeOpsAction, ScopeItem
from ai.backend.manager.data.resource.types import UserResourcePolicyData
from ai.backend.manager.models.resource_policy.row import UserResourcePolicyRow
from ai.backend.manager.models.resource_policy.scopes import UserResourcePolicyOperationScope
from ai.backend.manager.models.resource_policy.searchers import (
    UserResourcePolicySearcher,
)
from ai.backend.manager.models.scopes import OperationScope


@dataclass(frozen=True)
class UserResourcePolicyScopeItem(ScopeItem):
    """The user resource policies of one user."""

    user_id: UserID

    @override
    def scope_ref(self) -> ScopeRef:
        return ScopeRef(scope_type=USER_SCOPE_TYPE, scope_id=self.user_id)

    @override
    def operation_scope(self) -> OperationScope:
        return UserResourcePolicyOperationScope(user_id=self.user_id)


@dataclass
class SearchUserResourcePoliciesAction(
    OperationScopeOpsAction[UserResourcePolicyRow, UserResourcePolicyData]
):
    """Page through the user resource policies the named scopes reach, combined with
    OR.

    Which users those are, is the caller's business: the scopes are an argument.
    """

    items: Sequence[UserResourcePolicyScopeItem]
    searcher: UserResourcePolicySearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return UserResourcePolicyEntityType()

    @override
    def scope_targets(self) -> Sequence[ScopeRef]:
        return [item.scope_ref() for item in self.items]

    @override
    def operation_scopes(self) -> Sequence[OperationScope]:
        return [item.operation_scope() for item in self.items]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_user_resource_policies"

    @override
    def to_searcher(self) -> UserResourcePolicySearcher:
        return self.searcher
