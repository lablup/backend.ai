from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.entity.usage_bucket import PROJECT_USAGE_BUCKET_ENTITY_TYPE
from ai.backend.manager.actions.v2.ops.base import SearchGlobalOpsAction
from ai.backend.manager.data.resource_usage_history.types import ProjectUsageBucketData
from ai.backend.manager.models.resource_usage_history.row import ProjectUsageBucketRow
from ai.backend.manager.models.resource_usage_history.searchers import (
    ProjectUsageBucketSearcher,
)


@dataclass
class GlobalSearchProjectUsageBucketsAction(
    SearchGlobalOpsAction[ProjectUsageBucketRow, ProjectUsageBucketData]
):
    """Super-admin path: page through every project usage bucket."""

    searcher: ProjectUsageBucketSearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return PROJECT_USAGE_BUCKET_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_search_project_usage_buckets"

    @override
    def to_searcher(self) -> ProjectUsageBucketSearcher:
        return self.searcher
