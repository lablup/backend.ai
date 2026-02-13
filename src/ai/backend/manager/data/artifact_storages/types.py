from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, override

from ai.backend.common.data.storage.types import ArtifactStorageType
from ai.backend.common.types import ArtifactStorageId, ConcreteStorageId
from ai.backend.manager.errors.common import InternalServerError
from ai.backend.manager.models.artifact_storages import ArtifactStorageRow
from ai.backend.manager.repositories.base.creator import CreatorSpec
from ai.backend.manager.repositories.base.updater import UpdaterSpec
from ai.backend.manager.types import OptionalState


@dataclass(frozen=True)
class ArtifactStorageData:
    """Data class for ArtifactStorageRow."""

    id: ArtifactStorageId
    name: str
    storage_id: ConcreteStorageId
    type: ArtifactStorageType


class ArtifactStorageCreatorSpec(CreatorSpec[ArtifactStorageRow]):
    """CreatorSpec for ArtifactStorageRow with deferred storage_id."""

    def __init__(self, name: str, storage_type: ArtifactStorageType) -> None:
        self._name = name
        self._storage_type = storage_type
        self._storage_id: ConcreteStorageId | None = None

    def set_storage_id(self, storage_id: ConcreteStorageId) -> None:
        self._storage_id = storage_id

    @override
    def build_row(self) -> ArtifactStorageRow:
        if self._storage_id is None:
            raise InternalServerError("storage_id must be set before building row")
        return ArtifactStorageRow(
            name=self._name,
            storage_id=self._storage_id,
            type=self._storage_type,
        )


@dataclass
class ArtifactStorageUpdaterSpec(UpdaterSpec[ArtifactStorageRow]):
    """UpdaterSpec for ArtifactStorageRow."""

    name: OptionalState[str] = field(default_factory=OptionalState.nop)

    @property
    @override
    def row_class(self) -> type[ArtifactStorageRow]:
        return ArtifactStorageRow

    @override
    def build_values(self) -> dict[str, Any]:
        values: dict[str, Any] = {}
        self.name.update_dict(values, "name")
        return values
