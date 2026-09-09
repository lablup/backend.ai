from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.common.data.entity.user import UserEntityType
from ai.backend.manager.actions.v2.ops.base import OperationScopeOpsAction
from ai.backend.manager.data.resource_usage_history.types import UserUsageBucketData
from ai.backend.manager.models.resource_usage_history.row import UserUsageBucketRow
from ai.backend.manager.models.resource_usage_history.searchers import (
    UserUsageBucketSearcher,
)
from ai.backend.manager.models.scopes import OperationScope
from ai.backend.manager.services.resource_usage.actions.scope_items import (
    UserUsageBucketScopeItem,
)


@dataclass
class SearchUserUsageBucketsAction(
    OperationScopeOpsAction[UserUsageBucketRow, UserUsageBucketData]
):
    """Page through the user usage buckets the named resource groups hold, combined with OR."""

    items: Sequence[UserUsageBucketScopeItem]
    searcher: UserUsageBucketSearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return UserEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_user_usage_buckets"

    @override
    def scope_targets(self) -> Sequence[EntityIdentifier]:
        return [item.scope_ref() for item in self.items]

    @override
    def operation_scopes(self) -> Sequence[OperationScope]:
        return [item.operation_scope() for item in self.items]

    @override
    def to_searcher(self) -> UserUsageBucketSearcher:
        return self.searcher
