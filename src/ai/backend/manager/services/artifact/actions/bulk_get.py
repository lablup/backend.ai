from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.artifact import ArtifactID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import PartialBulkGetEntityOpsAction
from ai.backend.manager.data.artifact.types import ArtifactData
from ai.backend.manager.models.artifact.queriers import BulkArtifactQuerier
from ai.backend.manager.models.artifact.row import ArtifactRow


@dataclass
class BulkGetArtifactsAction(PartialBulkGetEntityOpsAction[ArtifactRow, ArtifactData]):
    """Read the artifacts the caller named, answering for each id."""

    ids: Sequence[ArtifactID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_get_artifacts"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(self.ids)

    @override
    def to_querier(self) -> BulkArtifactQuerier:
        return BulkArtifactQuerier()

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(self, ids=[entity_id for entity_id in self.ids if entity_id in allowed])
