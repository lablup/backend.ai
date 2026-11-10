from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import UpdatePartialBulkOpsAction
from ai.backend.manager.data.artifact.types import ArtifactData
from ai.backend.manager.models.artifact.row import ArtifactRow
from ai.backend.manager.models.artifact.updaters import ArtifactUpdater


@dataclass(frozen=True)
class PartialBulkUpdateArtifactsAction(UpdatePartialBulkOpsAction[ArtifactRow, ArtifactData]):
    """Edit the named artifacts' metadata, answering for each one."""

    updaters: Sequence[ArtifactUpdater]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "partial_bulk_update_artifacts"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(updater.artifact_id for updater in self.updaters)

    @override
    def to_updaters(self) -> Mapping[EntityIdentifier, ArtifactUpdater]:
        return {updater.artifact_id: updater for updater in self.updaters}

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(
            self, updaters=[updater for updater in self.updaters if updater.artifact_id in allowed]
        )
