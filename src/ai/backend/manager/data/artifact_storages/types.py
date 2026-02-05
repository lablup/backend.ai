from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, override

from ai.backend.common.data.storage.types import ArtifactStorageType
from ai.backend.manager.errors.common import InternalServerError
from ai.backend.manager.models.artifact_storages import ArtifactStorageRow
from ai.backend.manager.repositories.base.creator import CreatorSpec
from ai.backend.manager.repositories.base.updater import UpdaterSpec
from ai.backend.manager.types import OptionalState


class ArtifactStorageCreatorSpec(CreatorSpec[ArtifactStorageRow]):
    """CreatorSpec for ArtifactStorageRow with deferred storage_id."""

    def __init__(self, name: str, storage_type: ArtifactStorageType) -> None:
        self._name = name
        self._storage_type = storage_type
        self._storage_id: uuid.UUID | None = None

    def set_storage_id(self, storage_id: uuid.UUID) -> None:
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
    """UpdaterSpec for ArtifactStorageRow.

    Note: storage_id is used to find the ArtifactStorageRow (since it's unique),
    then the actual PK (id) is retrieved and used with execute_updater.
    """

    name: OptionalState[str] = field(default_factory=OptionalState.nop)
    storage_id: uuid.UUID | None = None

    @property
    @override
    def row_class(self) -> type[ArtifactStorageRow]:
        return ArtifactStorageRow

    @override
    def build_values(self) -> dict[str, Any]:
        values: dict[str, Any] = {}
        self.name.update_dict(values, "name")
        return values
