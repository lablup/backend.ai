from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import final, override

from ai.backend.common.data.entity.resource_policy import (
    KeyPairResourcePolicyEntityType,
)
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.manager.actions.v2.ops.base import OperationScopeOpsAction
from ai.backend.manager.data.resource.types import KeyPairResourcePolicyData
from ai.backend.manager.models.resource_policy.row import KeyPairResourcePolicyRow
from ai.backend.manager.models.resource_policy.scopes import UserKeypairResourcePolicyTarget
from ai.backend.manager.models.resource_policy.searchers import (
    KeyPairResourcePolicySearcher,
)
from ai.backend.manager.models.scopes import OperationScope


@dataclass
class SearchKeypairResourcePoliciesAction(
    OperationScopeOpsAction[KeyPairResourcePolicyRow, KeyPairResourcePolicyData]
):
    """Page through the keypair resource policies the named scopes reach, combined
    with OR.

    Which users those are, is the caller's business: the scopes are an argument.
    """

    targets: Sequence[UserKeypairResourcePolicyTarget]
    searcher: KeyPairResourcePolicySearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return KeyPairResourcePolicyEntityType()

    @final
    @override
    def scope_targets(self) -> Sequence[EntityIdentifier]:
        return [target.scope_id() for target in self.targets]

    @final
    @override
    def operation_scopes(self) -> Sequence[OperationScope]:
        return self.targets

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_keypair_resource_policies"

    @override
    def to_searcher(self) -> KeyPairResourcePolicySearcher:
        return self.searcher
