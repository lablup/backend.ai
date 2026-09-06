"""Delete spec for the reservoir_registries table."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.artifact_registry import ArtifactRegistryID
from ai.backend.manager.models.reservoir_registry.row import ReservoirRegistryRow
from ai.backend.manager.models.specs.purger import EntityPurger
from ai.backend.manager.models.specs.types import ConflictCheck


@dataclass
class ReservoirRegistryPurger(EntityPurger[ReservoirRegistryRow, ArtifactRegistryID]):
    """Remove a Reservoir registry and the node it was.

    Answers the id rather than the registry's values: the name it would report lives in
    the row deleted alongside it.
    """

    registry_id: ArtifactRegistryID

    @override
    def entity_id(self) -> ArtifactRegistryID:
        return self.registry_id

    @override
    def row_class(self) -> type[ReservoirRegistryRow]:
        return ReservoirRegistryRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return ReservoirRegistryRow.id

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: ReservoirRegistryRow) -> ArtifactRegistryID:
        return ArtifactRegistryID(row.id)
