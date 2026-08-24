"""Delete spec for the huggingface_registries table."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.artifact_registry import ArtifactRegistryID
from ai.backend.manager.models.huggingface_registry.row import HuggingFaceRegistryRow
from ai.backend.manager.models.specs.purger import EntityPurger
from ai.backend.manager.models.specs.types import ConflictCheck


@dataclass
class HuggingFaceRegistryPurger(EntityPurger[HuggingFaceRegistryRow, ArtifactRegistryID]):
    """Remove a HuggingFace registry and the node it was.

    Answers the id rather than the registry's values: the name it would report lives in
    the row deleted alongside it.
    """

    registry_id: ArtifactRegistryID

    @override
    def entity_id(self) -> ArtifactRegistryID:
        return self.registry_id

    @override
    def row_class(self) -> type[HuggingFaceRegistryRow]:
        return HuggingFaceRegistryRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return HuggingFaceRegistryRow.id

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: HuggingFaceRegistryRow) -> ArtifactRegistryID:
        return ArtifactRegistryID(row.id)
