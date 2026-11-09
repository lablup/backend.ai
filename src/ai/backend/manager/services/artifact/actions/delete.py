from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import DeleteSingleEntityOpsAction
from ai.backend.manager.data.artifact.types import ArtifactData
from ai.backend.manager.models.artifact.row import ArtifactRow
from ai.backend.manager.models.artifact.updaters import ArtifactSoftDeleteUpdater


@dataclass(frozen=True)
class DeleteArtifactAction(DeleteSingleEntityOpsAction[ArtifactRow, ArtifactData]):
    """Mark one artifact deleted."""

    updater: ArtifactSoftDeleteUpdater

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.updater.artifact_id

    @override
    @classmethod
    def action_name(cls) -> str:
        return "delete_artifact"

    @override
    def to_updater(self) -> ArtifactSoftDeleteUpdater:
        return self.updater
