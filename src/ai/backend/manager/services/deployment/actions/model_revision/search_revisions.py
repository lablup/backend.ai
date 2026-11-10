from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import BulkScopedSearchOpsAction
from ai.backend.manager.data.deployment.types import ModelRevisionData
from ai.backend.manager.models.deployment_revision.row import DeploymentRevisionRow
from ai.backend.manager.models.deployment_revision.scopes import (
    DeploymentRevisionTarget,
)
from ai.backend.manager.models.deployment_revision.searchers import ModelRevisionSearcher
from ai.backend.manager.models.scopes import OperationScope


@dataclass
class SearchRevisionsAction(BulkScopedSearchOpsAction[DeploymentRevisionRow, ModelRevisionData]):
    """Page through the revisions of the deployments named, combined with OR.

    Every deployment is authorized before the read runs. Reading every deployment's
    revisions is the global variant, which says so in its shape.
    """

    deployment_ids: Sequence[DeploymentID]
    searcher: ModelRevisionSearcher

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_revisions"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(self.deployment_ids)

    @override
    def operation_scopes(self) -> Sequence[OperationScope]:
        return [
            DeploymentRevisionTarget(deployment_id=deployment_id)
            for deployment_id in self.deployment_ids
        ]

    @override
    def to_searcher(self) -> ModelRevisionSearcher:
        return self.searcher
