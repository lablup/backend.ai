from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import GLOBAL_ENTITY_TYPE, EntityType
from ai.backend.manager.actions.v2.ops.base import SearchGlobalOpsAction
from ai.backend.manager.data.resource_usage_history.types import UserUsageBucketData
from ai.backend.manager.models.resource_usage_history.row import UserUsageBucketRow
from ai.backend.manager.models.resource_usage_history.searchers import (
    UserUsageBucketSearcher,
)


@dataclass
class GlobalSearchUserUsageBucketsAction(
    SearchGlobalOpsAction[UserUsageBucketRow, UserUsageBucketData]
):
    """Super-admin path: page through every user usage bucket."""

    searcher: UserUsageBucketSearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return GLOBAL_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_search_user_usage_buckets"

    @override
    def to_searcher(self) -> UserUsageBucketSearcher:
        return self.searcher
