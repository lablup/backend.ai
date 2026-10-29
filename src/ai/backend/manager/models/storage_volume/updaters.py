from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.entity.service_catalog import ServiceCatalogID
from ai.backend.common.data.entity.storage_volume import StorageVolumeID
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.updater import DataBatchUpdater
from ai.backend.manager.models.storage_volume.row import StorageVolumeServiceHoldingRow

__all__ = ("StorageVolumeHoldingStatusUpdater",)


@dataclass
class StorageVolumeHoldingStatusUpdater(
    DataBatchUpdater[StorageVolumeServiceHoldingRow, StorageVolumeID]
):
    """Write when a service last checked a volume it holds, or only touch the holding
    while ``status_checked_at`` is None."""

    service_catalog_id: ServiceCatalogID
    storage_volume_id: StorageVolumeID
    status_checked_at: datetime | None

    @property
    @override
    def row_class(self) -> type[StorageVolumeServiceHoldingRow]:
        return StorageVolumeServiceHoldingRow

    @override
    def conditions(self) -> list[QueryCondition]:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return (
                StorageVolumeServiceHoldingRow.service_catalog_id == self.service_catalog_id
            ) & (StorageVolumeServiceHoldingRow.storage_volume_id == self.storage_volume_id)

        return [inner]

    @override
    def build_values(self) -> dict[str, Any]:
        if self.status_checked_at is None:
            return {"updated_at": sa.func.now()}
        return {"status_checked_at": self.status_checked_at}

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def to_data(self, row: StorageVolumeServiceHoldingRow) -> StorageVolumeID:
        return StorageVolumeID(row.storage_volume_id)
