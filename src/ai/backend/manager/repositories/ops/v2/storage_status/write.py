from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence

import sqlalchemy as sa

from ai.backend.common.data.entity.service_catalog import ServiceCatalogID
from ai.backend.common.data.entity.storage_backend import StorageBackendID
from ai.backend.common.data.entity.storage_volume import StorageVolumeID, StorageVolumeName
from ai.backend.common.data.storage.types import StorageBackendType
from ai.backend.manager.errors.service_catalog import ServiceCatalogNotFound
from ai.backend.manager.models.service_catalog.row import ServiceCatalogRow
from ai.backend.manager.models.storage_backend.row import StorageBackendTypeRow
from ai.backend.manager.models.storage_backend.upserters import StorageBackendUpserter
from ai.backend.manager.models.storage_volume.row import (
    StorageVolumeRow,
    StorageVolumeServiceHoldingRow,
)
from ai.backend.manager.models.storage_volume.updaters import StorageVolumeHoldingStatusUpdater
from ai.backend.manager.models.storage_volume.upserters import (
    StorageVolumeHoldingUpserter,
    StorageVolumeUpserter,
)
from ai.backend.manager.repositories.ops.v2.relation.write import V2RelationWriteOps
from ai.backend.manager.repositories.ops.v2.storage_status.types import (
    VolumeStatusReportWrite,
    VolumeStatusWrite,
)


class V2StorageStatusWriteOps(V2RelationWriteOps):
    """The relation write ops plus the write of a service's storage status report."""

    async def record_volume_status_report(self, report: VolumeStatusReportWrite) -> None:
        """Insert each reported volume, its backend and its holding when absent, then write
        each holding's status. Raises :class:`ServiceCatalogNotFound` when the service has
        no catalog record."""
        service_id = await self._sess.scalar(
            sa.select(ServiceCatalogRow.id).where(
                (ServiceCatalogRow.service_group == report.service_group)
                & (ServiceCatalogRow.instance_id == report.instance_id)
            )
        )
        if service_id is None:
            raise ServiceCatalogNotFound(
                f"service_group={report.service_group}, instance_id={report.instance_id}"
            )
        service_id = ServiceCatalogID(service_id)
        volume_ids = await self._ensure_volumes(report.volumes)
        held = [
            (volume, volume_ids[volume.volume_name])
            for volume in report.volumes
            if volume.volume_name in volume_ids
        ]
        await self._ensure_holdings(service_id, [volume_id for _, volume_id in held])
        for volume, volume_id in held:
            await self.batch_update_in_global(
                StorageVolumeHoldingStatusUpdater(
                    service_catalog_id=service_id,
                    storage_volume_id=volume_id,
                    status=volume.status,
                    status_checked_at=volume.status_checked_at,
                )
            )

    async def _ensure_holdings(
        self, service_id: ServiceCatalogID, volume_ids: Collection[StorageVolumeID]
    ) -> None:
        """Link the service to each volume it does not hold yet, so only a new holding
        writes the graph."""
        held = set(
            await self._sess.scalars(
                sa.select(StorageVolumeServiceHoldingRow.storage_volume_id).where(
                    (StorageVolumeServiceHoldingRow.service_catalog_id == service_id)
                    & StorageVolumeServiceHoldingRow.storage_volume_id.in_(volume_ids)
                )
            )
        )
        await self.atomic_insert_relations_if_absent(
            StorageVolumeHoldingUpserter(),
            [(service_id, volume_id) for volume_id in volume_ids if volume_id not in held],
        )

    async def _volume_ids(
        self, names: Collection[StorageVolumeName]
    ) -> dict[StorageVolumeName, StorageVolumeID]:
        rows = await self._sess.execute(
            sa.select(StorageVolumeRow.name, StorageVolumeRow.id).where(
                StorageVolumeRow.name.in_(names)
            )
        )
        return {StorageVolumeName(name): volume_id for name, volume_id in rows}

    async def _ensure_volumes(
        self, volumes: Sequence[VolumeStatusWrite]
    ) -> Mapping[StorageVolumeName, StorageVolumeID]:
        """Ids of the volumes, inserting the absent ones. A volume whose backend type is not
        registered has no backend to link to and is left out."""
        volume_ids = await self._volume_ids({volume.volume_name for volume in volumes})
        absent = [volume for volume in volumes if volume.volume_name not in volume_ids]
        if not absent:
            return volume_ids
        backend_ids = await self._ensure_backends({volume.backend_type for volume in absent})
        upserters = [
            StorageVolumeUpserter(
                name=volume.volume_name, storage_backend_id=backend_ids[volume.backend_type]
            )
            for volume in absent
            if volume.backend_type in backend_ids
        ]
        results = await self.atomic_insert_entities_if_absent(upserters)
        for upserter, result in zip(upserters, results, strict=True):
            volume_ids[upserter.name] = StorageVolumeID(result.entity_id)
        return volume_ids

    async def _ensure_backends(
        self, backend_types: Collection[StorageBackendType]
    ) -> Mapping[StorageBackendType, StorageBackendID]:
        """Ids of the backends named after each registered type, inserting the absent ones."""
        type_rows = await self._sess.execute(
            sa.select(StorageBackendTypeRow.name, StorageBackendTypeRow.id).where(
                StorageBackendTypeRow.name.in_(backend_types)
            )
        )
        upserters = [
            StorageBackendUpserter(name=name, storage_backend_type_id=type_id)
            for name, type_id in type_rows
        ]
        results = await self.atomic_insert_entities_if_absent(upserters)
        return {
            StorageBackendType(upserter.name): StorageBackendID(result.entity_id)
            for upserter, result in zip(upserters, results, strict=True)
        }
