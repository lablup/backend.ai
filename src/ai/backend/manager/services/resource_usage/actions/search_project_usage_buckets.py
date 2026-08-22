from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.project import PROJECT_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType, ScopeRef
from ai.backend.manager.actions.v2.ops.base import OperationScopeOpsAction
from ai.backend.manager.data.resource_usage_history.types import ProjectUsageBucketData
from ai.backend.manager.models.resource_usage_history.row import ProjectUsageBucketRow
from ai.backend.manager.models.resource_usage_history.searchers import (
    ProjectUsageBucketSearcher,
)
from ai.backend.manager.models.scopes import OperationScope
from ai.backend.manager.repositories.resource_usage_history.types import (
    ProjectUsageBucketOperationScope,
)


@dataclass
class SearchProjectUsageBucketsAction(
    OperationScopeOpsAction[ProjectUsageBucketRow, ProjectUsageBucketData]
):
    """Page through the project usage buckets of one scope."""

    scope_target: ScopeRef
    scope: ProjectUsageBucketOperationScope
    searcher: ProjectUsageBucketSearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return PROJECT_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_project_usage_buckets"

    @override
    def scope_targets(self) -> Sequence[ScopeRef]:
        return (self.scope_target,)

    @override
    def operation_scopes(self) -> Sequence[OperationScope]:
        return (self.scope,)

    @override
    def to_searcher(self) -> ProjectUsageBucketSearcher:
        return self.searcher
