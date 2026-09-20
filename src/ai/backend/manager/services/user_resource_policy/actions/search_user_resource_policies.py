from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import final, override

from ai.backend.common.data.entity.resource_policy import (
    UserResourcePolicyEntityType,
)
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.manager.actions.v2.ops.base import OperationScopeOpsAction
from ai.backend.manager.data.resource.types import UserResourcePolicyData
from ai.backend.manager.models.resource_policy.row import UserResourcePolicyRow
from ai.backend.manager.models.resource_policy.scopes import UserResourcePolicyTarget
from ai.backend.manager.models.resource_policy.searchers import (
    UserResourcePolicySearcher,
)
from ai.backend.manager.models.scopes import OperationScope


@dataclass
class SearchUserResourcePoliciesAction(
    OperationScopeOpsAction[UserResourcePolicyRow, UserResourcePolicyData]
):
    """Page through the user resource policies the named scopes reach, combined with
    OR.

    Which users those are, is the caller's business: the scopes are an argument.
    """

    targets: Sequence[UserResourcePolicyTarget]
    searcher: UserResourcePolicySearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return UserResourcePolicyEntityType()

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
        return "search_user_resource_policies"

    @override
    def to_searcher(self) -> UserResourcePolicySearcher:
        return self.searcher
