from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.service_catalog import ServiceCatalogID
from ai.backend.common.data.entity.storage_volume import StorageVolumeID
from ai.backend.manager.errors.storage_volume import StorageVolumeHoldingNotFound
from ai.backend.manager.models.specs.types import GuardCheck, IntegrityErrorCheck
from ai.backend.manager.models.specs.updater import GuardedDataUpdater
from ai.backend.manager.models.storage_volume.row import StorageVolumeServiceHoldingRow

__all__ = ("StorageVolumeHoldingStatusUpdater",)


@dataclass
class StorageVolumeHoldingStatusUpdater(
    GuardedDataUpdater[StorageVolumeServiceHoldingRow, StorageVolumeID]
):
    """Write when a service last checked a volume it holds. The guard picks the reporting
    service's holding among those of the volume."""

    service_catalog_id: ServiceCatalogID
    storage_volume_id: StorageVolumeID
    status_checked_at: datetime

    @property
    @override
    def row_class(self) -> type[StorageVolumeServiceHoldingRow]:
        return StorageVolumeServiceHoldingRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return StorageVolumeServiceHoldingRow.storage_volume_id

    @override
    def target_id_value(self) -> StorageVolumeID:
        return self.storage_volume_id

    @override
    def guard_checks(self) -> Sequence[GuardCheck]:
        return (
            GuardCheck(
                condition=lambda: (
                    StorageVolumeServiceHoldingRow.service_catalog_id == self.service_catalog_id
                ),
                error=StorageVolumeHoldingNotFound(
                    f"service_catalog_id={self.service_catalog_id}, "
                    f"storage_volume_id={self.storage_volume_id}"
                ),
            ),
        )

    @override
    def build_values(self) -> dict[str, Any]:
        return {"status_checked_at": self.status_checked_at}

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def to_data(self, row: StorageVolumeServiceHoldingRow) -> StorageVolumeID:
        return StorageVolumeID(row.storage_volume_id)
