from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.artifact_registry import ArtifactRegistryID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import PartialBulkGetEntityOpsAction
from ai.backend.manager.data.artifact_registries.types import ArtifactRegistryData
from ai.backend.manager.models.artifact_registries.queriers import BulkArtifactRegistryQuerier
from ai.backend.manager.models.artifact_registries.row import ArtifactRegistryRow


@dataclass
class GetArtifactRegistryMetasAction(
    PartialBulkGetEntityOpsAction[ArtifactRegistryRow, ArtifactRegistryData]
):
    """Read the artifact registries the caller named, answering for each id."""

    registry_ids: Sequence[ArtifactRegistryID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_artifact_registry_metas"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(self.registry_ids)

    @override
    def to_querier(self) -> BulkArtifactRegistryQuerier:
        return BulkArtifactRegistryQuerier()

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(self, registry_ids=[rid for rid in self.registry_ids if rid in allowed])
