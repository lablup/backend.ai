"""Insert spec for the reservoir_registries table."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.artifact_registry import ArtifactRegistryID
from ai.backend.manager.data.reservoir_registry.types import ReservoirRegistryData
from ai.backend.manager.models.reservoir_registry.row import ReservoirRegistryRow
from ai.backend.manager.models.specs.creator import GlobalEntityCreator
from ai.backend.manager.models.specs.types import IntegrityErrorCheck


@dataclass
class ReservoirRegistryCreator(GlobalEntityCreator[ReservoirRegistryRow, ReservoirRegistryData]):
    """Register a Reservoir registry.

    The node is provisioned on this row's id, and the name is read through the relation
    the registry ops loads, as for a HuggingFace registry.
    """

    endpoint: str
    access_key: str
    secret_key: str
    api_version: str

    @override
    def entity_id(self, row: ReservoirRegistryRow) -> ArtifactRegistryID:
        return ArtifactRegistryID(row.id)

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_row(self) -> ReservoirRegistryRow:
        return ReservoirRegistryRow(
            endpoint=self.endpoint,
            access_key=self.access_key,
            secret_key=self.secret_key,
            api_version=self.api_version,
        )

    @override
    def to_data(self, row: ReservoirRegistryRow) -> ReservoirRegistryData:
        return row.to_dataclass()
