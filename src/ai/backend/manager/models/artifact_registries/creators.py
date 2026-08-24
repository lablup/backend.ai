"""Insert spec for the artifact_registries table."""

from __future__ import annotations

from dataclasses import dataclass

from ai.backend.common.data.artifact.types import ArtifactRegistryType
from ai.backend.common.data.entity.artifact_registry import ArtifactRegistryID
from ai.backend.manager.data.artifact_registries.types import ArtifactRegistryData
from ai.backend.manager.models.artifact_registries.row import ArtifactRegistryRow


@dataclass
class ArtifactRegistryMetaCreator:
    """Insert spec of the row naming a registry and saying which kind it is.

    Outside the v2 creator roots on purpose: the row is no entity — the node lives on
    the per-type registry row its ``registry_id`` names — and no field row either, whose
    roots bind their data type to ``FieldData``. The registry ops is its only executor.
    """

    name: str
    type: ArtifactRegistryType

    def build_row(self, registry_id: ArtifactRegistryID) -> ArtifactRegistryRow:
        return ArtifactRegistryRow(
            name=self.name,
            registry_id=registry_id,
            type=self.type.value,
        )

    def to_data(self, row: ArtifactRegistryRow) -> ArtifactRegistryData:
        return row.to_dataclass()
