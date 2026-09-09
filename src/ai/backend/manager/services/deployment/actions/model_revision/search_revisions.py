from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.deployment import DeploymentEntityType, DeploymentID
from ai.backend.common.data.entity.types import EntityType, ScopeRef, ScopeType
from ai.backend.manager.actions.v2.ops.base import OperationScopeOpsAction
from ai.backend.manager.data.deployment.types import ModelRevisionData
from ai.backend.manager.models.deployment_revision.row import DeploymentRevisionRow
from ai.backend.manager.models.deployment_revision.scopes import (
    DeploymentRevisionOperationScope,
)
from ai.backend.manager.models.deployment_revision.searchers import ModelRevisionSearcher
from ai.backend.manager.models.scopes import OperationScope


@dataclass
class SearchRevisionsAction(OperationScopeOpsAction[DeploymentRevisionRow, ModelRevisionData]):
    """Page through the revisions of one deployment.

    The deployment is the scope, so ops applies that condition. Reading every
    deployment's revisions is the global variant, which says so in its shape.
    """

    deployment_id: DeploymentID
    searcher: ModelRevisionSearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return DeploymentEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_revisions"

    @override
    def scope_targets(self) -> Sequence[ScopeRef]:
        return (
            ScopeRef(scope_type=ScopeType(DeploymentEntityType()), scope_id=self.deployment_id),
        )

    @override
    def operation_scopes(self) -> Sequence[OperationScope]:
        return (DeploymentRevisionOperationScope(deployment_id=self.deployment_id),)

    @override
    def to_searcher(self) -> ModelRevisionSearcher:
        return self.searcher
