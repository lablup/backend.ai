from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence

import sqlalchemy as sa

from ai.backend.common.data.entity.service_catalog import ServiceCatalogID
from ai.backend.common.data.entity.storage_backend import StorageBackendID
from ai.backend.common.data.entity.storage_volume import StorageVolumeID, StorageVolumeName
from ai.backend.common.data.storage.types import StorageBackendMetadata, StorageBackendType
from ai.backend.manager.errors.service_catalog import ServiceCatalogNotFound
from ai.backend.manager.models.service_catalog.row import ServiceCatalogRow
from ai.backend.manager.models.specs.types import BulkResultWithFailures
from ai.backend.manager.models.storage_backend.upserters import (
    StorageBackendTypeUpserter,
    StorageBackendUpserter,
)
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
    ServiceVolumeStatusReport,
    VolumeStatusRecord,
)


class V2StorageStatusWriteOps(V2RelationWriteOps):
    """The relation write ops plus the write of a service's storage status report."""

    async def record_volume_status_report(
        self, report: ServiceVolumeStatusReport
    ) -> BulkResultWithFailures[StorageVolumeID]:
        """Insert each reported volume, its backend and its holding when absent, then write
        the check time of each checked holding, answering per volume. Raises
        :class:`ServiceCatalogNotFound` when the service has no catalog record."""
        service_id = await self._sess.scalar(
            sa.select(ServiceCatalogRow.id).where(
                (ServiceCatalogRow.service_group == report.service_catalog_service_group)
                & (ServiceCatalogRow.instance_id == report.service_catalog_instance_id)
            )
        )
        if service_id is None:
            raise ServiceCatalogNotFound(
                f"service_group={report.service_catalog_service_group}, "
                f"instance_id={report.service_catalog_instance_id}"
            )
        service_id = ServiceCatalogID(service_id)
        volume_ids = await self._ensure_volumes(report.volumes)
        held = [
            (volume, volume_ids[volume.volume_name])
            for volume in report.volumes
            if volume.volume_name in volume_ids
        ]
        await self._ensure_holdings(service_id, [volume_id for _, volume_id in held])
        return await self.partial_bulk_update_data({
            volume_id: StorageVolumeHoldingStatusUpdater(
                service_catalog_id=service_id,
                storage_volume_id=volume_id,
                status_checked_at=volume.check_started_at,
            )
            for volume, volume_id in held
            if volume.check_started_at is not None
        })

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
        self, volumes: Sequence[VolumeStatusRecord]
    ) -> Mapping[StorageVolumeName, StorageVolumeID]:
        """Ids of the volumes, inserting the absent ones with their backends."""
        volume_ids = await self._volume_ids({volume.volume_name for volume in volumes})
        absent = [volume for volume in volumes if volume.volume_name not in volume_ids]
        if not absent:
            return volume_ids
        backend_ids = await self._ensure_backends({
            volume.storage_backend_metadata.name: volume.storage_backend_metadata
            for volume in absent
        })
        upserters = [
            StorageVolumeUpserter(
                name=volume.volume_name,
                storage_backend_id=backend_ids[volume.storage_backend_metadata.name],
            )
            for volume in absent
        ]
        results = await self.atomic_insert_entities_if_absent(upserters)
        for upserter, result in zip(upserters, results, strict=True):
            volume_ids[upserter.name] = StorageVolumeID(result.entity_id)
        return volume_ids

    async def _ensure_backends(
        self, metadata: Mapping[StorageBackendType, StorageBackendMetadata]
    ) -> Mapping[StorageBackendType, StorageBackendID]:
        """Ids of the backends named after each type, upserting the types with their reported
        capabilities and inserting the absent backends."""
        types = await self.atomic_upsert_entities([
            StorageBackendTypeUpserter(name=data.name, capabilities=data.capabilities)
            for data in metadata.values()
        ])
        upserters = [
            StorageBackendUpserter(name=data.name, storage_backend_type_id=data.id)
            for data in types
        ]
        results = await self.atomic_insert_entities_if_absent(upserters)
        return {
            StorageBackendType(upserter.name): StorageBackendID(result.entity_id)
            for upserter, result in zip(upserters, results, strict=True)
        }
