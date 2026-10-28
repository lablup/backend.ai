from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.service_catalog import ServiceCatalogID
from ai.backend.common.data.entity.storage_backend import StorageBackendID
from ai.backend.common.data.entity.storage_volume import StorageVolumeID, StorageVolumeName
from ai.backend.manager.models.specs.created_in import CreatedInGlobal
from ai.backend.manager.models.specs.relation import RelationUpserter
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.upserter import EntityUpserter
from ai.backend.manager.models.storage_volume.row import (
    StorageVolumeRow,
    StorageVolumeServiceHoldingRow,
)

__all__ = (
    "StorageVolumeHoldingUpserter",
    "StorageVolumeUpserter",
)


@dataclass
class StorageVolumeUpserter(
    CreatedInGlobal[StorageVolumeRow], EntityUpserter[StorageVolumeRow, StorageVolumeID]
):
    """Upsert spec for one storage volume.

    Conflict key: ``name``. A volume already there is left as it stands.
    """

    name: StorageVolumeName
    storage_backend_id: StorageBackendID

    @override
    def entity_id(self, row: StorageVolumeRow) -> StorageVolumeID:
        return StorageVolumeID(row.id)

    @override
    def row_class(self) -> type[StorageVolumeRow]:
        return StorageVolumeRow

    @override
    def index_elements(self) -> list[str]:
        return ["name"]

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_insert_values(self) -> dict[str, Any]:
        return {"name": self.name, "storage_backend_id": self.storage_backend_id}

    @override
    def build_update_values(self) -> dict[str, Any]:
        return {}

    @override
    def to_data(self, row: StorageVolumeRow) -> StorageVolumeID:
        return StorageVolumeID(row.id)


@dataclass
class StorageVolumeHoldingUpserter(
    RelationUpserter[ServiceCatalogID, StorageVolumeID, StorageVolumeServiceHoldingRow]
):
    """Link a service to a volume it holds, not checked yet. A pair already linked is
    left as it stands."""

    @override
    def row_class(self) -> type[StorageVolumeServiceHoldingRow]:
        return StorageVolumeServiceHoldingRow

    @override
    def index_elements(self) -> list[str]:
        return ["service_catalog_id", "storage_volume_id"]

    @override
    def build_insert_values(
        self, scope: ServiceCatalogID, target: StorageVolumeID
    ) -> dict[str, Any]:
        return {
            "service_catalog_id": scope,
            "storage_volume_id": target,
            "status": None,
            "status_checked_at": None,
        }

    @override
    def build_update_values(self) -> dict[str, Any]:
        return {}

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()
