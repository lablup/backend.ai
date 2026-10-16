from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import RestoreSingleEntityOpsAction
from ai.backend.manager.data.artifact.types import ArtifactData
from ai.backend.manager.models.artifact.row import ArtifactRow
from ai.backend.manager.models.artifact.updaters import ArtifactRestoreUpdater


@dataclass(frozen=True)
class RestoreArtifactAction(RestoreSingleEntityOpsAction[ArtifactRow, ArtifactData]):
    """Mark one deleted artifact alive again."""

    updater: ArtifactRestoreUpdater

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.updater.artifact_id

    @override
    @classmethod
    def action_name(cls) -> str:
        return "restore_artifact"

    @override
    def to_updater(self) -> ArtifactRestoreUpdater:
        return self.updater
