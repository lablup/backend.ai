from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.deployment import DeploymentEntityType
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import SearchGlobalOpsAction
from ai.backend.manager.data.deployment.types import ModelRevisionData
from ai.backend.manager.models.deployment_revision.row import DeploymentRevisionRow
from ai.backend.manager.models.deployment_revision.searchers import ModelRevisionSearcher


@dataclass
class GlobalSearchRevisionsAction(SearchGlobalOpsAction[DeploymentRevisionRow, ModelRevisionData]):
    """Page through model revisions across every deployment."""

    searcher: ModelRevisionSearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return DeploymentEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_search_revisions"

    @override
    def to_searcher(self) -> ModelRevisionSearcher:
        return self.searcher
