from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.artifact import ArtifactID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import BulkScopedSearchOpsAction
from ai.backend.manager.data.artifact.types import ArtifactRevisionData
from ai.backend.manager.models.artifact_revision.row import ArtifactRevisionRow
from ai.backend.manager.models.artifact_revision.scopes import ArtifactRevisionTarget
from ai.backend.manager.models.artifact_revision.searchers import ArtifactRevisionSearcher
from ai.backend.manager.models.scopes import OperationScope


@dataclass
class GetArtifactRevisionsAction(
    BulkScopedSearchOpsAction[ArtifactRevisionRow, ArtifactRevisionData]
):
    """Page through the revisions of the artifacts named, combined with OR.

    Every artifact is authorized before the read runs.
    """

    artifact_ids: Sequence[ArtifactID]
    searcher: ArtifactRevisionSearcher

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_artifact_revisions"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(self.artifact_ids)

    @override
    def operation_scopes(self) -> Sequence[OperationScope]:
        return [
            ArtifactRevisionTarget(artifact_id=artifact_id) for artifact_id in self.artifact_ids
        ]

    @override
    def to_searcher(self) -> ArtifactRevisionSearcher:
        return self.searcher
