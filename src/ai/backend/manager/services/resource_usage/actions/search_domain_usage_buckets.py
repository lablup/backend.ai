from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import final, override

from ai.backend.common.data.entity.domain import DomainEntityType
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.manager.actions.v2.ops.base import OperationScopeOpsAction
from ai.backend.manager.data.resource_usage_history.types import DomainUsageBucketData
from ai.backend.manager.models.resource_usage_history.row import DomainUsageBucketRow
from ai.backend.manager.models.resource_usage_history.scopes import (
    DomainUsageBucketTarget,
)
from ai.backend.manager.models.resource_usage_history.searchers import (
    DomainUsageBucketSearcher,
)
from ai.backend.manager.models.scopes import OperationScope


@dataclass
class SearchDomainUsageBucketsAction(
    OperationScopeOpsAction[DomainUsageBucketRow, DomainUsageBucketData]
):
    """Page through the domain usage buckets the named resource groups hold, combined with OR."""

    targets: Sequence[DomainUsageBucketTarget]
    searcher: DomainUsageBucketSearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return DomainEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_domain_usage_buckets"

    @final
    @override
    def scope_targets(self) -> Sequence[EntityIdentifier]:
        return [target.scope_id() for target in self.targets]

    @final
    @override
    def operation_scopes(self) -> Sequence[OperationScope]:
        return self.targets

    @override
    def to_searcher(self) -> DomainUsageBucketSearcher:
        return self.searcher
