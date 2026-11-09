from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.artifact import ArtifactID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import DeletePartialBulkOpsAction
from ai.backend.manager.data.artifact.types import ArtifactData
from ai.backend.manager.models.artifact.row import ArtifactRow
from ai.backend.manager.models.artifact.updaters import ArtifactSoftDeleteUpdater


@dataclass(frozen=True)
class PartialBulkDeleteArtifactsAction(DeletePartialBulkOpsAction[ArtifactRow, ArtifactData]):
    """Mark the named artifacts deleted, answering for each one."""

    ids: Sequence[ArtifactID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "partial_bulk_delete_artifacts"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(self.ids)

    @override
    def to_updaters(self) -> Mapping[EntityIdentifier, ArtifactSoftDeleteUpdater]:
        return {
            artifact_id: ArtifactSoftDeleteUpdater(artifact_id=artifact_id)
            for artifact_id in self.ids
        }

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(
            self, ids=[artifact_id for artifact_id in self.ids if artifact_id in allowed]
        )
