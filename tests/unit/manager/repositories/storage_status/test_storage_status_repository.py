from __future__ import annotations

from collections.abc import AsyncGenerator, Sequence
from datetime import UTC, datetime

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.service_catalog import ServiceCatalogID
from ai.backend.common.data.entity.storage_volume import StorageVolumeName
from ai.backend.common.data.storage.types import (
    StorageBackendCapabilities,
    StorageBackendCapability,
    StorageBackendMetadata,
    StorageBackendType,
)
from ai.backend.manager.errors.service_catalog import ServiceCatalogNotFound
from ai.backend.manager.models.service_catalog.row import (
    ServiceCatalogEndpointRow,
    ServiceCatalogRow,
)
from ai.backend.manager.models.service_catalog.upserters import ServiceCatalogUpserter
from ai.backend.manager.models.storage_backend.row import StorageBackendRow, StorageBackendTypeRow
from ai.backend.manager.models.storage_volume.row import (
    StorageVolumeRow,
    StorageVolumeServiceHoldingRow,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.entity_membership_cap import EntityMembershipCapRow
from ai.backend.manager.models.virtual_entity.entity_membership_field import (
    EntityMembershipFieldRow,
)
from ai.backend.manager.models.virtual_entity.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.ops.v2.storage_status.provider import StorageStatusOpsProvider
from ai.backend.manager.repositories.ops.v2.storage_status.types import (
    ServiceVolumeStatusReport,
    VolumeStatusRecord,
)
from ai.backend.manager.repositories.service_catalog.repository import ServiceCatalogRepository
from ai.backend.manager.repositories.storage_status.repository import StorageStatusRepository
from ai.backend.testutils.db import with_tables

SERVICE_GROUP = "storage-proxy"
FIRST_INSTANCE_ID = "storage-proxy-1"
SECOND_INSTANCE_ID = "storage-proxy-2"

VFS = StorageBackendMetadata(
    name=StorageBackendType("vfs"),
    capabilities=StorageBackendCapabilities(
        supported=frozenset({StorageBackendCapability.VFOLDER})
    ),
)
XFS = StorageBackendMetadata(
    name=StorageBackendType("xfs"),
    capabilities=StorageBackendCapabilities(supported=frozenset({StorageBackendCapability.QUOTA})),
)
VFS_WITH_METRIC = StorageBackendMetadata(
    name=VFS.name,
    capabilities=StorageBackendCapabilities(
        supported=frozenset({StorageBackendCapability.VFOLDER, StorageBackendCapability.METRIC})
    ),
)

CHECKED_AT = datetime(2026, 10, 30, 9, 0, tzinfo=UTC)
LATER_CHECKED_AT = datetime(2026, 10, 30, 9, 1, tzinfo=UTC)


def _volume(
    name: str,
    metadata: StorageBackendMetadata = VFS,
    check_started_at: datetime | None = CHECKED_AT,
) -> VolumeStatusRecord:
    return VolumeStatusRecord(
        volume_name=StorageVolumeName(name),
        storage_backend_metadata=metadata,
        check_started_at=check_started_at,
    )


def _report(
    volumes: Sequence[VolumeStatusRecord],
    instance_id: str = FIRST_INSTANCE_ID,
) -> ServiceVolumeStatusReport:
    return ServiceVolumeStatusReport(
        service_catalog_service_group=SERVICE_GROUP,
        service_catalog_instance_id=instance_id,
        volumes=volumes,
    )


async def _count(db: ExtendedAsyncSAEngine, row_class: type[object]) -> int:
    async with db.begin_readonly_session() as session:
        count = await session.scalar(sa.select(sa.func.count()).select_from(row_class))
    assert count is not None
    return count


async def _holding_checked_at(
    db: ExtendedAsyncSAEngine, service_id: ServiceCatalogID, volume_name: str
) -> datetime | None:
    async with db.begin_readonly_session() as session:
        return await session.scalar(
            sa.select(StorageVolumeServiceHoldingRow.status_checked_at)
            .join(
                StorageVolumeRow,
                StorageVolumeRow.id == StorageVolumeServiceHoldingRow.storage_volume_id,
            )
            .where(
                (StorageVolumeServiceHoldingRow.service_catalog_id == service_id)
                & (StorageVolumeRow.name == volume_name)
            )
        )


async def _backend_type_capabilities(
    db: ExtendedAsyncSAEngine, name: StorageBackendType
) -> StorageBackendCapabilities | None:
    async with db.begin_readonly_session() as session:
        capabilities: StorageBackendCapabilities | None = await session.scalar(
            sa.select(StorageBackendTypeRow.capabilities).where(StorageBackendTypeRow.name == name)
        )
    return capabilities


async def _volume_backend_name(db: ExtendedAsyncSAEngine, volume_name: str) -> str | None:
    async with db.begin_readonly_session() as session:
        name: str | None = await session.scalar(
            sa.select(StorageBackendRow.name)
            .join(StorageVolumeRow, StorageVolumeRow.storage_backend_id == StorageBackendRow.id)
            .where(StorageVolumeRow.name == volume_name)
        )
    return name


class TestStorageStatusRepositoryRecordVolumeStatusReport:
    @pytest.fixture
    async def db_with_tables(
        self,
        global_entity_ids: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            global_entity_ids,
            [
                ServiceCatalogRow,
                ServiceCatalogEndpointRow,
                StorageBackendTypeRow,
                StorageBackendRow,
                StorageVolumeRow,
                StorageVolumeServiceHoldingRow,
                VirtualEntityRow,
                EntityMembershipRow,
                EntityMembershipCapRow,
                EntityMembershipFieldRow,
                ScopeBindingRow,
            ],
        ):
            yield global_entity_ids

    async def _register_service(
        self, db: ExtendedAsyncSAEngine, instance_id: str
    ) -> ServiceCatalogID:
        return await ServiceCatalogRepository(V2DBOpsProvider(db)).register(
            ServiceCatalogUpserter(
                service_group=SERVICE_GROUP,
                instance_id=instance_id,
                display_name=instance_id,
                version="1",
                labels={},
                startup_time=CHECKED_AT,
                config_hash="",
            ),
            [],
        )

    @pytest.fixture
    async def first_service_id(self, db_with_tables: ExtendedAsyncSAEngine) -> ServiceCatalogID:
        return await self._register_service(db_with_tables, FIRST_INSTANCE_ID)

    @pytest.fixture
    async def second_service_id(self, db_with_tables: ExtendedAsyncSAEngine) -> ServiceCatalogID:
        return await self._register_service(db_with_tables, SECOND_INSTANCE_ID)

    @pytest.fixture
    def repository(self, db_with_tables: ExtendedAsyncSAEngine) -> StorageStatusRepository:
        return StorageStatusRepository(StorageStatusOpsProvider(db_with_tables))

    async def test_first_report_creates_backend_volume_and_holding(
        self,
        repository: StorageStatusRepository,
        db_with_tables: ExtendedAsyncSAEngine,
        first_service_id: ServiceCatalogID,
    ) -> None:
        await repository.record_volume_status_report(_report([_volume("local")]))

        assert await _count(db_with_tables, StorageBackendTypeRow) == 1
        assert await _count(db_with_tables, StorageBackendRow) == 1
        assert await _count(db_with_tables, StorageVolumeRow) == 1
        assert await _holding_checked_at(db_with_tables, first_service_id, "local") == CHECKED_AT

    async def test_volumes_of_one_backend_type_share_one_backend(
        self,
        repository: StorageStatusRepository,
        db_with_tables: ExtendedAsyncSAEngine,
        first_service_id: ServiceCatalogID,
    ) -> None:
        await repository.record_volume_status_report(
            _report([_volume("local"), _volume("shared"), _volume("scratch")])
        )

        assert await _count(db_with_tables, StorageBackendTypeRow) == 1
        assert await _count(db_with_tables, StorageBackendRow) == 1
        assert await _count(db_with_tables, StorageVolumeRow) == 3
        assert await _count(db_with_tables, StorageVolumeServiceHoldingRow) == 3

    async def test_volumes_of_different_backend_types_get_their_own_backends(
        self,
        repository: StorageStatusRepository,
        db_with_tables: ExtendedAsyncSAEngine,
        first_service_id: ServiceCatalogID,
    ) -> None:
        await repository.record_volume_status_report(
            _report([_volume("local", VFS), _volume("fast", XFS)])
        )

        assert await _count(db_with_tables, StorageBackendRow) == 2
        assert await _volume_backend_name(db_with_tables, "local") == "vfs"
        assert await _volume_backend_name(db_with_tables, "fast") == "xfs"

    async def test_same_report_twice_writes_no_duplicate(
        self,
        repository: StorageStatusRepository,
        db_with_tables: ExtendedAsyncSAEngine,
        first_service_id: ServiceCatalogID,
    ) -> None:
        report = _report([_volume("local"), _volume("fast", XFS)])
        await repository.record_volume_status_report(report)

        await repository.record_volume_status_report(report)

        assert await _count(db_with_tables, StorageBackendTypeRow) == 2
        assert await _count(db_with_tables, StorageBackendRow) == 2
        assert await _count(db_with_tables, StorageVolumeRow) == 2
        assert await _count(db_with_tables, StorageVolumeServiceHoldingRow) == 2

    async def test_backend_type_capabilities_change_only_with_a_new_volume(
        self,
        repository: StorageStatusRepository,
        db_with_tables: ExtendedAsyncSAEngine,
        first_service_id: ServiceCatalogID,
    ) -> None:
        await repository.record_volume_status_report(_report([_volume("local")]))

        await repository.record_volume_status_report(_report([_volume("local", VFS_WITH_METRIC)]))
        assert await _backend_type_capabilities(db_with_tables, VFS.name) == VFS.capabilities

        await repository.record_volume_status_report(
            _report([_volume("local", VFS_WITH_METRIC), _volume("shared", VFS_WITH_METRIC)])
        )
        assert (
            await _backend_type_capabilities(db_with_tables, VFS.name)
            == VFS_WITH_METRIC.capabilities
        )

    async def test_later_check_overwrites_checked_at(
        self,
        repository: StorageStatusRepository,
        db_with_tables: ExtendedAsyncSAEngine,
        first_service_id: ServiceCatalogID,
    ) -> None:
        await repository.record_volume_status_report(_report([_volume("local")]))

        await repository.record_volume_status_report(
            _report([_volume("local", check_started_at=LATER_CHECKED_AT)])
        )

        assert (
            await _holding_checked_at(db_with_tables, first_service_id, "local") == LATER_CHECKED_AT
        )

    async def test_services_reporting_one_volume_hold_it_separately(
        self,
        repository: StorageStatusRepository,
        db_with_tables: ExtendedAsyncSAEngine,
        first_service_id: ServiceCatalogID,
        second_service_id: ServiceCatalogID,
    ) -> None:
        await repository.record_volume_status_report(_report([_volume("shared")]))

        await repository.record_volume_status_report(
            _report(
                [_volume("shared", check_started_at=LATER_CHECKED_AT)],
                instance_id=SECOND_INSTANCE_ID,
            )
        )

        assert await _count(db_with_tables, StorageVolumeRow) == 1
        assert await _holding_checked_at(db_with_tables, first_service_id, "shared") == CHECKED_AT
        assert (
            await _holding_checked_at(db_with_tables, second_service_id, "shared")
            == LATER_CHECKED_AT
        )

    async def test_not_checked_volume_is_held_without_checked_at(
        self,
        repository: StorageStatusRepository,
        db_with_tables: ExtendedAsyncSAEngine,
        first_service_id: ServiceCatalogID,
    ) -> None:
        await repository.record_volume_status_report(
            _report([_volume("local", check_started_at=None)])
        )

        assert await _count(db_with_tables, StorageVolumeServiceHoldingRow) == 1
        assert await _holding_checked_at(db_with_tables, first_service_id, "local") is None

    async def test_not_checked_report_keeps_previous_checked_at(
        self,
        repository: StorageStatusRepository,
        db_with_tables: ExtendedAsyncSAEngine,
        first_service_id: ServiceCatalogID,
    ) -> None:
        await repository.record_volume_status_report(_report([_volume("local")]))

        await repository.record_volume_status_report(
            _report([_volume("local", check_started_at=None)])
        )

        assert await _holding_checked_at(db_with_tables, first_service_id, "local") == CHECKED_AT

    async def test_registered_volume_keeps_its_backend(
        self,
        repository: StorageStatusRepository,
        db_with_tables: ExtendedAsyncSAEngine,
        first_service_id: ServiceCatalogID,
    ) -> None:
        await repository.record_volume_status_report(_report([_volume("local", VFS)]))

        await repository.record_volume_status_report(_report([_volume("local", XFS)]))

        assert await _volume_backend_name(db_with_tables, "local") == "vfs"

    async def test_empty_report_writes_nothing(
        self,
        repository: StorageStatusRepository,
        db_with_tables: ExtendedAsyncSAEngine,
        first_service_id: ServiceCatalogID,
    ) -> None:
        await repository.record_volume_status_report(_report([]))

        assert await _count(db_with_tables, StorageBackendTypeRow) == 0
        assert await _count(db_with_tables, StorageBackendRow) == 0
        assert await _count(db_with_tables, StorageVolumeRow) == 0
        assert await _count(db_with_tables, StorageVolumeServiceHoldingRow) == 0

    async def test_unknown_service_raises_and_writes_nothing(
        self,
        repository: StorageStatusRepository,
        db_with_tables: ExtendedAsyncSAEngine,
    ) -> None:
        with pytest.raises(ServiceCatalogNotFound):
            await repository.record_volume_status_report(_report([_volume("local")]))

        assert await _count(db_with_tables, StorageBackendTypeRow) == 0
        assert await _count(db_with_tables, StorageBackendRow) == 0
        assert await _count(db_with_tables, StorageVolumeRow) == 0
