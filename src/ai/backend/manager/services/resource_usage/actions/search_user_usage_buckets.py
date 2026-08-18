from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityType, ScopeRef
from ai.backend.common.data.entity.usage_bucket import USER_USAGE_BUCKET_ENTITY_TYPE
from ai.backend.manager.actions.v2.ops.base import OperationScopeOpsAction
from ai.backend.manager.data.resource_usage_history.types import UserUsageBucketData
from ai.backend.manager.models.resource_usage_history.row import UserUsageBucketRow
from ai.backend.manager.models.resource_usage_history.searchers import (
    UserUsageBucketSearcher,
)
from ai.backend.manager.models.scopes import OperationScope
from ai.backend.manager.repositories.resource_usage_history.types import (
    UserUsageBucketOperationScope,
)


@dataclass
class SearchUserUsageBucketsAction(
    OperationScopeOpsAction[UserUsageBucketRow, UserUsageBucketData]
):
    """Page through the user usage buckets of one scope."""

    scope_target: ScopeRef
    scope: UserUsageBucketOperationScope
    searcher: UserUsageBucketSearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return USER_USAGE_BUCKET_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_user_usage_buckets"

    @override
    def scope_targets(self) -> Sequence[ScopeRef]:
        return (self.scope_target,)

    @override
    def operation_scopes(self) -> Sequence[OperationScope]:
        return (self.scope,)

    @override
    def to_searcher(self) -> UserUsageBucketSearcher:
        return self.searcher
