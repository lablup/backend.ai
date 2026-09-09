from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.artifact import ArtifactEntityType, ArtifactID
from ai.backend.common.data.entity.types import EntityType, ScopeRef, ScopeType
from ai.backend.manager.actions.v2.ops.base import OperationScopeOpsAction
from ai.backend.manager.data.artifact.types import ArtifactRevisionData
from ai.backend.manager.models.artifact_revision.row import ArtifactRevisionRow
from ai.backend.manager.models.artifact_revision.scopes import ArtifactRevisionOperationScope
from ai.backend.manager.models.artifact_revision.searchers import ArtifactRevisionSearcher
from ai.backend.manager.models.scopes import OperationScope


@dataclass
class GetArtifactRevisionsAction(
    OperationScopeOpsAction[ArtifactRevisionRow, ArtifactRevisionData]
):
    """Page through the revisions of one artifact.

    The artifact is the scope, so ops applies that condition.
    """

    artifact_id: ArtifactID
    searcher: ArtifactRevisionSearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return ArtifactEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_artifact_revisions"

    @override
    def scope_targets(self) -> Sequence[ScopeRef]:
        return (ScopeRef(scope_type=ScopeType(ArtifactEntityType()), scope_id=self.artifact_id),)

    @override
    def operation_scopes(self) -> Sequence[OperationScope]:
        return (ArtifactRevisionOperationScope(artifact_id=self.artifact_id),)

    @override
    def to_searcher(self) -> ArtifactRevisionSearcher:
        return self.searcher
