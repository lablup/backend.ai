"""Update spec for the artifact_registries table."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, override
from uuid import UUID

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.artifact_registry import ArtifactRegistryID
from ai.backend.manager.data.artifact_registries.types import ArtifactRegistryData
from ai.backend.manager.models.artifact_registries.row import ArtifactRegistryRow
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.updater import DataUpdater
from ai.backend.manager.types import OptionalState


@dataclass
class ArtifactRegistryMetaUpdater(DataUpdater[ArtifactRegistryRow, ArtifactRegistryData]):
    """Rename a registry. Keyed by the registry the row names, not by its own id."""

    registry_id: ArtifactRegistryID
    name: OptionalState[str] = field(default_factory=OptionalState.nop)

    @property
    @override
    def row_class(self) -> type[ArtifactRegistryRow]:
        return ArtifactRegistryRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return ArtifactRegistryRow.registry_id

    @override
    def target_id_value(self) -> UUID:
        return self.registry_id

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.name.update_dict(to_update, "name")
        return to_update

    @override
    def to_data(self, row: ArtifactRegistryRow) -> ArtifactRegistryData:
        return row.to_dataclass()
