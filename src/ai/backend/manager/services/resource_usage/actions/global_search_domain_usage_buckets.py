from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.entity.usage_bucket import DOMAIN_USAGE_BUCKET_ENTITY_TYPE
from ai.backend.manager.actions.v2.ops.base import SearchGlobalOpsAction
from ai.backend.manager.data.resource_usage_history.types import DomainUsageBucketData
from ai.backend.manager.models.resource_usage_history.row import DomainUsageBucketRow
from ai.backend.manager.models.resource_usage_history.searchers import (
    DomainUsageBucketSearcher,
)


@dataclass
class GlobalSearchDomainUsageBucketsAction(
    SearchGlobalOpsAction[DomainUsageBucketRow, DomainUsageBucketData]
):
    """Super-admin path: page through every domain usage bucket."""

    searcher: DomainUsageBucketSearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return DOMAIN_USAGE_BUCKET_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_search_domain_usage_buckets"

    @override
    def to_searcher(self) -> DomainUsageBucketSearcher:
        return self.searcher
