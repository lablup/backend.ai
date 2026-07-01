"""
Tests for VFSStorageRepository functionality.
Tests the repository layer with real database operations.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest

# ORM relationship cluster registration: SQLAlchemy's global
# configure_mappers() must resolve every string relationship reachable from
# the rows this isolated test registers, so the whole domain cluster is
# imported here. _ORM_CLUSTER below keeps these imports from being pruned.
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.association_container_registries_groups import (
    AssociationContainerRegistriesGroupsRow,
)
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.deployment_auto_scaling_policy import DeploymentAutoScalingPolicyRow
from ai.backend.manager.models.deployment_policy import DeploymentPolicyRow
from ai.backend.manager.models.deployment_revision import DeploymentRevisionRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.endpoint import (
    EndpointAutoScalingRuleRow,
    EndpointRow,
    EndpointTokenRow,
)
from ai.backend.manager.models.fair_share import (
    DomainFairShareRow,
    ProjectFairShareRow,
    UserFairShareRow,
)
from ai.backend.manager.models.group import AssocGroupUserRow, GroupRow
from ai.backend.manager.models.image import ImageAliasRow, ImageRow
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.network import NetworkRow
from ai.backend.manager.models.notification import NotificationChannelRow, NotificationRuleRow
from ai.backend.manager.models.rbac_models import (
    AssociationScopesEntitiesRow,
    ObjectPermissionRow,
    RoleRow,
    UserRoleRow,
)
from ai.backend.manager.models.replica_group import ReplicaGroupRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.resource_preset import ResourcePresetRow
from ai.backend.manager.models.resource_slot import (
    AgentResourceRow,
    DeploymentRevisionResourceSlotRow,
    ResourceSlotTypeRow,
)
from ai.backend.manager.models.resource_usage_history import (
    DomainUsageBucketRow,
    KernelUsageRecordRow,
    ProjectUsageBucketRow,
    UserUsageBucketRow,
)
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.models.runtime_variant import RuntimeVariantRow
from ai.backend.manager.models.runtime_variant_preset import RuntimeVariantPresetRow
from ai.backend.manager.models.scaling_group import (
    ScalingGroupForDomainRow,
    ScalingGroupForKeypairsRow,
    ScalingGroupForProjectRow,
    ScalingGroupRow,
)
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import VFolderInvitationRow, VFolderPermissionRow, VFolderRow
from ai.backend.manager.models.vfs_storage import VFSStorageRow
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.manager.repositories.vfs_storage.repository import VFSStorageRepository
from ai.backend.testutils.db import with_tables

_ORM_CLUSTER = (
    AgentResourceRow,
    AgentRow,
    AssocGroupUserRow,
    AssociationContainerRegistriesGroupsRow,
    AssociationScopesEntitiesRow,
    ContainerRegistryRow,
    DeploymentAutoScalingPolicyRow,
    DeploymentPolicyRow,
    DeploymentRevisionResourceSlotRow,
    DeploymentRevisionRow,
    DomainFairShareRow,
    DomainRow,
    DomainUsageBucketRow,
    EndpointAutoScalingRuleRow,
    EndpointRow,
    EndpointTokenRow,
    GroupRow,
    ImageAliasRow,
    ImageRow,
    KernelRow,
    KernelUsageRecordRow,
    KeyPairResourcePolicyRow,
    KeyPairRow,
    NetworkRow,
    NotificationChannelRow,
    NotificationRuleRow,
    ObjectPermissionRow,
    ProjectFairShareRow,
    ProjectResourcePolicyRow,
    ProjectUsageBucketRow,
    ReplicaGroupRow,
    ResourcePresetRow,
    ResourceSlotTypeRow,
    RoleRow,
    RoutingRow,
    RuntimeVariantPresetRow,
    RuntimeVariantRow,
    ScalingGroupForDomainRow,
    ScalingGroupForKeypairsRow,
    ScalingGroupForProjectRow,
    ScalingGroupRow,
    SessionRow,
    UserFairShareRow,
    UserResourcePolicyRow,
    UserRoleRow,
    UserRow,
    UserUsageBucketRow,
    VFolderInvitationRow,
    VFolderPermissionRow,
    VFolderRow,
)


class TestVFSStorageRepository:
    """Test cases for VFSStorageRepository"""

    # =========================================================================
    # Fixtures
    # =========================================================================

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        """Database connection with tables created. TRUNCATE CASCADE handles cleanup."""
        async with with_tables(
            database_connection,
            [VFSStorageRow],
        ):
            yield database_connection

    @pytest.fixture
    def vfs_storage_repository(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> VFSStorageRepository:
        """Create a VFSStorageRepository instance"""
        return VFSStorageRepository(db_with_cleanup)

    @pytest.fixture
    async def sample_vfs_storage_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[uuid.UUID, None]:
        """Create sample VFS storage directly in DB and return its ID"""
        storage_id = uuid.uuid4()

        async with db_with_cleanup.begin_session() as db_sess:
            storage = VFSStorageRow(
                id=storage_id,
                name="test-vfs-storage",
                host="localhost",
                base_path="/mnt/vfs/test",
            )
            db_sess.add(storage)
            await db_sess.flush()

        yield storage_id

    @pytest.fixture
    async def sample_vfs_storages_for_filtering(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[dict[str, uuid.UUID], None]:
        """Create sample VFS storages with different hosts for filter testing"""
        storage_map: dict[str, uuid.UUID] = {}
        hosts = ["host-a", "host-b"]

        async with db_with_cleanup.begin_session() as db_sess:
            for i, host in enumerate(hosts):
                storage_id = uuid.uuid4()
                storage = VFSStorageRow(
                    id=storage_id,
                    name=f"filter-test-storage-{host}-{i}",
                    host=host,
                    base_path=f"/mnt/vfs/{host}",
                )
                db_sess.add(storage)
                storage_map[host] = storage_id
            await db_sess.flush()

        yield storage_map

    @pytest.fixture
    async def sample_vfs_storages_for_ordering(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[list[uuid.UUID], None]:
        """Create sample VFS storages with predictable names for ordering tests"""
        storage_ids = []
        names = ["alpha-storage", "beta-storage", "gamma-storage", "delta-storage"]

        async with db_with_cleanup.begin_session() as db_sess:
            for name in names:
                storage_id = uuid.uuid4()
                storage = VFSStorageRow(
                    id=storage_id,
                    name=name,
                    host="localhost",
                    base_path=f"/mnt/vfs/{name}",
                )
                db_sess.add(storage)
                storage_ids.append(storage_id)
            await db_sess.flush()

        yield storage_ids

    @pytest.fixture
    async def sample_vfs_storages_for_pagination(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[list[uuid.UUID], None]:
        """Create 25 VFS storages for pagination testing"""
        storage_ids = []

        async with db_with_cleanup.begin_session() as db_sess:
            for i in range(25):
                storage_id = uuid.uuid4()
                storage = VFSStorageRow(
                    id=storage_id,
                    name=f"pagination-test-storage-{i:02d}",
                    host="localhost",
                    base_path=f"/mnt/vfs/pagination/{i:02d}",
                )
                db_sess.add(storage)
                storage_ids.append(storage_id)
            await db_sess.flush()

        yield storage_ids

    # =========================================================================
    # Tests - Search with filtering
    # =========================================================================

    async def test_search_vfs_storages_filter_by_host(
        self,
        vfs_storage_repository: VFSStorageRepository,
        sample_vfs_storages_for_filtering: dict[str, uuid.UUID],
    ) -> None:
        """Test searching VFS storages filtered by host returns only matching storages"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[
                # TODO: Refactor after adding Condition type
                lambda: VFSStorageRow.host == "host-a",
            ],
            orders=[],
        )

        result = await vfs_storage_repository.search(querier=querier)

        result_storage_ids = [storage.id for storage in result.items]
        assert sample_vfs_storages_for_filtering["host-a"] in result_storage_ids
        assert sample_vfs_storages_for_filtering["host-b"] not in result_storage_ids

    async def test_search_vfs_storages_filter_by_name_pattern(
        self,
        vfs_storage_repository: VFSStorageRepository,
        sample_vfs_storages_for_ordering: list[uuid.UUID],
    ) -> None:
        """Test searching VFS storages with name pattern filter"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[
                # TODO: Refactor after adding Condition type
                lambda: VFSStorageRow.name.like("alpha%"),
            ],
            orders=[],
        )

        result = await vfs_storage_repository.search(querier=querier)

        assert len(result.items) == 1
        assert result.items[0].name == "alpha-storage"

    # =========================================================================
    # Tests - Search with ordering
    # =========================================================================

    async def test_search_vfs_storages_order_by_name_ascending(
        self,
        vfs_storage_repository: VFSStorageRepository,
        sample_vfs_storages_for_ordering: list[uuid.UUID],
    ) -> None:
        """Test searching VFS storages ordered by name ascending"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[VFSStorageRow.name.asc()],
        )

        result = await vfs_storage_repository.search(querier=querier)

        result_names = [storage.name for storage in result.items]
        assert result_names == sorted(result_names)
        assert result_names[0] == "alpha-storage"
        assert result_names[-1] == "gamma-storage"

    async def test_search_vfs_storages_order_by_name_descending(
        self,
        vfs_storage_repository: VFSStorageRepository,
        sample_vfs_storages_for_ordering: list[uuid.UUID],
    ) -> None:
        """Test searching VFS storages ordered by name descending"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[VFSStorageRow.name.desc()],
        )

        result = await vfs_storage_repository.search(querier=querier)

        result_names = [storage.name for storage in result.items]
        assert result_names == sorted(result_names, reverse=True)
        assert result_names[0] == "gamma-storage"
        assert result_names[-1] == "alpha-storage"

    # =========================================================================
    # Tests - Search with pagination
    # =========================================================================

    async def test_search_vfs_storages_offset_pagination_first_page(
        self,
        vfs_storage_repository: VFSStorageRepository,
        sample_vfs_storages_for_pagination: list[uuid.UUID],
    ) -> None:
        """Test first page of offset-based pagination"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[],
        )

        result = await vfs_storage_repository.search(querier=querier)

        assert len(result.items) == 10
        assert result.total_count == 25

    async def test_search_vfs_storages_offset_pagination_second_page(
        self,
        vfs_storage_repository: VFSStorageRepository,
        sample_vfs_storages_for_pagination: list[uuid.UUID],
    ) -> None:
        """Test second page of offset-based pagination"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=10),
            conditions=[],
            orders=[],
        )

        result = await vfs_storage_repository.search(querier=querier)

        assert len(result.items) == 10
        assert result.total_count == 25

    async def test_search_vfs_storages_offset_pagination_last_page(
        self,
        vfs_storage_repository: VFSStorageRepository,
        sample_vfs_storages_for_pagination: list[uuid.UUID],
    ) -> None:
        """Test last page of offset-based pagination with partial results"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=20),
            conditions=[],
            orders=[],
        )

        result = await vfs_storage_repository.search(querier=querier)

        assert len(result.items) == 5
        assert result.total_count == 25

    # =========================================================================
    # Tests - Search with combined query
    # =========================================================================

    async def test_search_vfs_storages_with_pagination_filter_and_order(
        self,
        vfs_storage_repository: VFSStorageRepository,
        sample_vfs_storages_for_pagination: list[uuid.UUID],
    ) -> None:
        """Test searching VFS storages with pagination, filter condition, and ordering combined"""
        # Filter: only storages with localhost host
        # Order: by name ascending
        # Pagination: limit 5, offset 2
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=5, offset=2),
            conditions=[
                # TODO: Refactor after adding Condition type
                lambda: VFSStorageRow.host == "localhost",
            ],
            orders=[VFSStorageRow.name.asc()],
        )

        result = await vfs_storage_repository.search(querier=querier)

        # Total localhost storages: 25, so total_count should be 25
        assert result.total_count == 25
        # With limit=5, offset=2, we get items at indices 2, 3, 4, 5, 6 of sorted results
        assert len(result.items) == 5

        # Verify ordering is ascending
        result_names = [storage.name for storage in result.items]
        assert result_names == sorted(result_names)
