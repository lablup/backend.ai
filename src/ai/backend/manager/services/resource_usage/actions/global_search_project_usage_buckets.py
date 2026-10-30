from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityType, GlobalEntityType
from ai.backend.manager.actions.v2.ops.base import GlobalSearcherOpsAction
from ai.backend.manager.data.resource_usage_history.types import ProjectUsageBucketData
from ai.backend.manager.models.resource_usage_history.row import ProjectUsageBucketRow


@dataclass(frozen=True)
class GlobalSearchProjectUsageBucketsAction(
    GlobalSearcherOpsAction[ProjectUsageBucketRow, ProjectUsageBucketData]
):
    """Super-admin path: page through every project usage bucket."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return GlobalEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_search_project_usage_buckets"
