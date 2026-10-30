from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityType, GlobalEntityType
from ai.backend.manager.actions.v2.ops.base import GlobalSearcherOpsAction
from ai.backend.manager.data.resource_usage_history.types import DomainUsageBucketData
from ai.backend.manager.models.resource_usage_history.row import DomainUsageBucketRow


@dataclass(frozen=True)
class GlobalSearchDomainUsageBucketsAction(
    GlobalSearcherOpsAction[DomainUsageBucketRow, DomainUsageBucketData]
):
    """Super-admin path: page through every domain usage bucket."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return GlobalEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_search_domain_usage_buckets"
