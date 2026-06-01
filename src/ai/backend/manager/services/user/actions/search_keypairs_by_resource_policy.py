from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import EntityType, RBACElementType, ScopeType
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.action.scope import BaseScopeAction
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.common.types import SearchResult
from ai.backend.manager.data.keypair.types import KeyPairData
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.repositories.base.querier import BatchQuerier
from ai.backend.manager.repositories.keypair.types import KeypairResourcePolicySearchScope


@dataclass
class SearchKeypairsByResourcePolicyAction(BaseScopeAction):
    """Action for searching keypairs assigned to a keypair resource policy.

    RBAC validation checks if the user has READ permission on the keypair
    resource policy scope. Superadmins bypass the check; other users must hold
    a role granting read access, so a regular user cannot enumerate keypairs
    owned by others through the resource policy node.
    """

    scope: KeypairResourcePolicySearchScope
    querier: BatchQuerier

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.KEYPAIR

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.KEYPAIR

    @override
    def scope_id(self) -> str:
        return self.scope.resource_policy_name

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(
            RBACElementType.KEYPAIR_RESOURCE_POLICY, self.scope.resource_policy_name
        )


@dataclass
class SearchKeypairsByResourcePolicyActionResult(BaseActionResult):
    """Result of searching keypairs by resource policy."""

    result: SearchResult[KeyPairData]

    @override
    def entity_id(self) -> str | None:
        return None
