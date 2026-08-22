from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.resource_policy import (
    KEYPAIR_RESOURCE_POLICY_ENTITY_TYPE,
)
from ai.backend.common.data.entity.types import EntityType, ScopeRef
from ai.backend.common.data.entity.user import USER_SCOPE_TYPE, UserID
from ai.backend.manager.actions.v2.ops.base import OperationScopeOpsAction
from ai.backend.manager.data.resource.types import KeyPairResourcePolicyData
from ai.backend.manager.models.resource_policy.row import KeyPairResourcePolicyRow
from ai.backend.manager.models.resource_policy.searchers import (
    KeyPairResourcePolicySearcher,
)
from ai.backend.manager.models.scopes import OperationScope
from ai.backend.manager.repositories.keypair_resource_policy.types import (
    UserKeypairResourcePolicyOperationScope,
)


@dataclass
class SearchKeypairResourcePoliciesAction(
    OperationScopeOpsAction[KeyPairResourcePolicyRow, KeyPairResourcePolicyData]
):
    """Page through the keypair resource policies that apply within a user scope.

    Which user that is, is the caller's business: the scope is an argument.
    """

    user_id: UserID
    searcher: KeyPairResourcePolicySearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return KEYPAIR_RESOURCE_POLICY_ENTITY_TYPE

    @override
    def scope_targets(self) -> Sequence[ScopeRef]:
        return (ScopeRef(scope_type=USER_SCOPE_TYPE, scope_id=self.user_id),)

    @override
    def operation_scopes(self) -> Sequence[OperationScope]:
        return (UserKeypairResourcePolicyOperationScope(user_id=self.user_id),)

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_keypair_resource_policies"

    @override
    def to_searcher(self) -> KeyPairResourcePolicySearcher:
        return self.searcher
