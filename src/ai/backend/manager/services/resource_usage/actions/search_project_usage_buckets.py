from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import final, override

from ai.backend.common.data.entity.project import ProjectEntityType
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.manager.actions.v2.ops.base import OperationScopeOpsAction
from ai.backend.manager.data.resource_usage_history.types import ProjectUsageBucketData
from ai.backend.manager.models.resource_usage_history.row import ProjectUsageBucketRow
from ai.backend.manager.models.resource_usage_history.scopes import (
    ProjectUsageBucketTarget,
)
from ai.backend.manager.models.resource_usage_history.searchers import (
    ProjectUsageBucketSearcher,
)
from ai.backend.manager.models.scopes import OperationScope


@dataclass
class SearchProjectUsageBucketsAction(
    OperationScopeOpsAction[ProjectUsageBucketRow, ProjectUsageBucketData]
):
    """Page through the project usage buckets the named resource groups hold, combined with OR."""

    targets: Sequence[ProjectUsageBucketTarget]
    searcher: ProjectUsageBucketSearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return ProjectEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_project_usage_buckets"

    @final
    @override
    def scope_targets(self) -> Sequence[EntityIdentifier]:
        return [target.scope_id() for target in self.targets]

    @final
    @override
    def operation_scopes(self) -> Sequence[OperationScope]:
        return self.targets

    @override
    def to_searcher(self) -> ProjectUsageBucketSearcher:
        return self.searcher
