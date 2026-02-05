from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any, override

from ai.backend.common.data.storage.types import ArtifactStorageType
from ai.backend.manager.repositories.base.creator import CreatorSpec
from ai.backend.manager.repositories.base.updater import UpdaterSpec
from ai.backend.manager.types import OptionalState

if TYPE_CHECKING:
    from ai.backend.manager.models.artifact_storages import ArtifactStorageRow


class ArtifactStorageCreatorSpec(CreatorSpec["ArtifactStorageRow"]):
    """CreatorSpec for ArtifactStorageRow with deferred storage_id."""

    def __init__(self, name: str, storage_type: ArtifactStorageType) -> None:
        self._name = name
        self._storage_type = storage_type
        self._storage_id: uuid.UUID | None = None

    def set_storage_id(self, storage_id: uuid.UUID) -> None:
        self._storage_id = storage_id

    @override
    def build_row(self) -> ArtifactStorageRow:
        from ai.backend.manager.models.artifact_storages import ArtifactStorageRow  # noqa: PLC0415

        if self._storage_id is None:
            raise ValueError("storage_id must be set before building row")
        return ArtifactStorageRow(
            name=self._name,
            storage_id=self._storage_id,
            type=self._storage_type,
        )


class ArtifactStorageUpdaterSpec(UpdaterSpec["ArtifactStorageRow"]):
    """UpdaterSpec for ArtifactStorageRow.

    Note: This spec uses storage_id (the FK to ObjectStorageRow/VFSStorageRow) to find
    the ArtifactStorageRow, not the ArtifactStorageRow's own PK. The db_source layer
    handles this by querying with storage_id and applying updates via apply_to_row().
    """

    def __init__(self, name: OptionalState[str], storage_id: uuid.UUID) -> None:
        self._name = name
        self._storage_id = storage_id

    @property
    def storage_id(self) -> uuid.UUID:
        return self._storage_id

    @property
    @override
    def row_class(self) -> type[ArtifactStorageRow]:
        from ai.backend.manager.models.artifact_storages import ArtifactStorageRow  # noqa: PLC0415

        return ArtifactStorageRow

    @override
    def build_values(self) -> dict[str, Any]:
        values: dict[str, Any] = {}
        if (name := self._name.optional_value()) is not None:
            values["name"] = name
        return values
