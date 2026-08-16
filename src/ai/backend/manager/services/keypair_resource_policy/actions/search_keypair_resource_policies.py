from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.resource_policy import (
    KEYPAIR_RESOURCE_POLICY_ENTITY_TYPE,
)
from ai.backend.common.data.entity.types import EntityType, ScopeRef
from ai.backend.common.data.entity.user import USER_SCOPE_TYPE
from ai.backend.manager.actions.v2.ops.base import OperationScopeOpsAction
from ai.backend.manager.data.resource.types import KeyPairResourcePolicyData
from ai.backend.manager.models.resource_policy.row import KeyPairResourcePolicyRow
from ai.backend.manager.models.scopes import OperationScope
from ai.backend.manager.repositories.keypair_resource_policy.searchers import (
    KeyPairResourcePolicySearcher,
)
from ai.backend.manager.repositories.keypair_resource_policy.types import (
    UserKeypairResourcePolicyOperationScope,
)


@dataclass
class SearchKeypairResourcePoliciesAction(
    OperationScopeOpsAction[KeyPairResourcePolicyRow, KeyPairResourcePolicyData]
):
    """Read the policies in effect within the scopes the caller names.

    A scope names a user, never a keypair.
    """

    scopes: Sequence[UserKeypairResourcePolicyOperationScope]
    searcher: KeyPairResourcePolicySearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return KEYPAIR_RESOURCE_POLICY_ENTITY_TYPE

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
        return "search_keypair_resource_policies"

    @override
    def to_searcher(self) -> KeyPairResourcePolicySearcher:
        return self.searcher
