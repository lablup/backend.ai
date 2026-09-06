"""Update spec for the reservoir_registries table."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, override
from uuid import UUID

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.artifact_registry import ArtifactRegistryID
from ai.backend.manager.data.reservoir_registry.types import ReservoirRegistryData
from ai.backend.manager.models.reservoir_registry.row import ReservoirRegistryRow
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.updater import DataUpdater
from ai.backend.manager.types import OptionalState


@dataclass
class ReservoirRegistryUpdater(DataUpdater[ReservoirRegistryRow, ReservoirRegistryData]):
    """Edit a Reservoir registry. The name is the meta row's and is not written here."""

    registry_id: ArtifactRegistryID
    endpoint: OptionalState[str] = field(default_factory=OptionalState.nop)
    access_key: OptionalState[str] = field(default_factory=OptionalState.nop)
    secret_key: OptionalState[str] = field(default_factory=OptionalState.nop)
    api_version: OptionalState[str] = field(default_factory=OptionalState.nop)

    @property
    @override
    def row_class(self) -> type[ReservoirRegistryRow]:
        return ReservoirRegistryRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return ReservoirRegistryRow.id

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
        self.endpoint.update_dict(to_update, "endpoint")
        self.access_key.update_dict(to_update, "access_key")
        self.secret_key.update_dict(to_update, "secret_key")
        self.api_version.update_dict(to_update, "api_version")
        return to_update

    @override
    def to_data(self, row: ReservoirRegistryRow) -> ReservoirRegistryData:
        return row.to_dataclass()
