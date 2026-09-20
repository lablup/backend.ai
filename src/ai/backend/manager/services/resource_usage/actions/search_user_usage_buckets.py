from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import final, override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.common.data.entity.user import UserEntityType
from ai.backend.manager.actions.v2.ops.base import OperationScopeOpsAction
from ai.backend.manager.data.resource_usage_history.types import UserUsageBucketData
from ai.backend.manager.models.resource_usage_history.row import UserUsageBucketRow
from ai.backend.manager.models.resource_usage_history.scopes import (
    UserUsageBucketTarget,
)
from ai.backend.manager.models.resource_usage_history.searchers import (
    UserUsageBucketSearcher,
)
from ai.backend.manager.models.scopes import OperationScope


@dataclass
class SearchUserUsageBucketsAction(
    OperationScopeOpsAction[UserUsageBucketRow, UserUsageBucketData]
):
    """Page through the user usage buckets the named resource groups hold, combined with OR."""

    targets: Sequence[UserUsageBucketTarget]
    searcher: UserUsageBucketSearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return UserEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_user_usage_buckets"

    @final
    @override
    def scope_targets(self) -> Sequence[EntityIdentifier]:
        return [target.scope_id() for target in self.targets]

    @final
    @override
    def operation_scopes(self) -> Sequence[OperationScope]:
        return self.targets

    @override
    def to_searcher(self) -> UserUsageBucketSearcher:
        return self.searcher
