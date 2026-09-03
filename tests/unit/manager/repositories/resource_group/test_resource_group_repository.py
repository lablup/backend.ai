import uuid
from collections.abc import AsyncGenerator, Callable
from datetime import UTC, datetime
from typing import Any

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.resource_group import ResourceGroupID, ResourceGroupName
from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.common.exception import ResourceGroupConflict
from ai.backend.common.types import (
    AccessKey,
    DefaultForUnspecified,
    PreemptionVictimScope,
    ResourceSlot,
    SessionTypes,
)
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.data.resource_group.types import PreemptionConfig as DataPreemptionConfig
from ai.backend.manager.data.user.types import UserStatus
from ai.backend.manager.errors.resource import (
    DefaultResourceGroupAlreadyExists,
    ResourceGroupNotFound,
)
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.deployment_auto_scaling_policy import DeploymentAutoScalingPolicyRow
from ai.backend.manager.models.deployment_policy import DeploymentPolicyRow
from ai.backend.manager.models.deployment_revision import DeploymentRevisionRow
from ai.backend.manager.models.deployment_revision_preset import DeploymentRevisionPresetRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.models.entity_label.row import EntityLabelRow
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.project import ProjectRow
from ai.backend.manager.models.rbac_models import AssociationScopesEntitiesRow, RoleRow, UserRoleRow
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role_permission_preset.row import (
    RolePermissionPresetRow,
)
from ai.backend.manager.models.rbac_models.role_preset.row import RolePresetRow
from ai.backend.manager.models.replica_group import ReplicaGroupRow
from ai.backend.manager.models.resource_group import (
    ResourceGroupForDomainRow,
    ResourceGroupForKeypairsRow,
    ResourceGroupForProjectRow,
    ResourceGroupOpts,
    ResourceGroupRow,
)
from ai.backend.manager.models.resource_group.creators import ResourceGroupCreator
from ai.backend.manager.models.resource_group.updaters import ResourceGroupUpdater
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.resource_preset import ResourcePresetRow
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.models.runtime_variant import RuntimeVariantRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.specs.pagination import OffsetPagination
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import VFolderRow
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.entity_membership_cap import (
    EntityMembershipCapRow,
)
from ai.backend.manager.models.virtual_entity.entity_membership_field import (
    EntityMembershipFieldRow,
)
from ai.backend.manager.models.virtual_entity.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.repositories.base.creator import BulkCreator
from ai.backend.manager.repositories.base.rbac.scope_binder import (
    RBACScopeBinder,
    RBACScopeBindingPair,
)
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.resource_group import ResourceGroupRepository
from ai.backend.manager.repositories.resource_group.creators import (
    ResourceGroupForDomainCreatorSpec,
    ResourceGroupForKeypairsCreatorSpec,
    ResourceGroupForProjectCreatorSpec,
)
from ai.backend.manager.repositories.resource_group.purgers import (
    create_resource_group_for_keypairs_purger,
)
from ai.backend.manager.repositories.resource_group.scope_binders import (
    ResourceGroupDomainEntityUnbinder,
    ResourceGroupProjectEntityUnbinder,
)
from ai.backend.manager.secret.types import SecretValue
from ai.backend.manager.types import OptionalState, TriState
from ai.backend.testutils.db import with_tables
from ai.backend.testutils.fixtures import DomainFactory, DomainFixtureData


class TestScalingGroupRepositoryDB:
    """Test cases for ResourceGroupRepository"""

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        """Database connection with tables created. TRUNCATE CASCADE handles cleanup."""
        async with with_tables(
            database_connection,
            [
                # FK dependency order: parents before children
                DomainRow,
                ResourceGroupRow,
                AssociationScopesEntitiesRow,
                RoleRow,
                UserRoleRow,
                PermissionRow,
                RolePresetRow,
                RolePermissionPresetRow,
                VirtualEntityRow,
                EntityMembershipRow,
                EntityMembershipCapRow,
                EntityMembershipFieldRow,
                ScopeBindingRow,
                EntityLabelRow,
                ResourceGroupForDomainRow,
                ResourceGroupForProjectRow,
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                KeyPairResourcePolicyRow,
                UserRow,
                KeyPairRow,
                ResourceGroupForKeypairsRow,  # depends on ResourceGroupRow and KeyPairRow
                ProjectRow,
                ContainerRegistryRow,
                ImageRow,
                VFolderRow,
                EndpointRow,
                DeploymentPolicyRow,
                DeploymentAutoScalingPolicyRow,
                RuntimeVariantRow,
                DeploymentRevisionPresetRow,
                DeploymentRevisionRow,
                SessionRow,
                AgentRow,
                KernelRow,
                ReplicaGroupRow,
                RoutingRow,
                ResourcePresetRow,
            ],
        ):
            yield database_connection

    def _create_scaling_group_creator(
        self,
        name: str,
        driver: str = "static",
        scheduler: str = "fifo",
        description: str | None = None,
        is_active: bool = True,
        is_public: bool = True,
        is_default: bool = False,
        wsproxy_addr: str | None = None,
        wsproxy_api_token: str | None = None,
        driver_opts: dict[str, Any] | None = None,
        scheduler_opts: ResourceGroupOpts | None = None,
        use_host_network: bool = False,
    ) -> ResourceGroupCreator:
        """Build a ResourceGroupCreator with the given parameters."""
        return ResourceGroupCreator(
            name=name,
            driver=driver,
            scheduler=scheduler,
            description=description,
            is_active=is_active,
            is_public=is_public,
            is_default=is_default,
            wsproxy_addr=wsproxy_addr,
            wsproxy_api_token=wsproxy_api_token,
            driver_opts=driver_opts if driver_opts is not None else {},
            scheduler_opts=scheduler_opts,
            use_host_network=use_host_network,
        )

    async def _create_scaling_groups(
        self,
        db_engine: ExtendedAsyncSAEngine,
        count: int,
        is_active_func: Callable[[int], bool] = lambda i: True,
    ) -> list[str]:
        """Helper to create scaling groups with given parameters"""
        resource_group_names = []
        async with db_engine.begin_session() as db_sess:
            for i in range(count):
                sgroup_name = f"{uuid.uuid4()}"
                sgroup = ResourceGroupRow(
                    name=sgroup_name,
                    description=f"Test scaling group {i:02d}",
                    is_active=is_active_func(i),
                    is_public=True,
                    created_at=datetime.now(tz=UTC),
                    wsproxy_addr=None,
                    wsproxy_api_token=None,
                    driver="static",
                    driver_opts={},
                    scheduler="fifo",
                    scheduler_opts=ResourceGroupOpts(),
                    use_host_network=False,
                )
                db_sess.add(sgroup)
                resource_group_names.append(sgroup_name)
            await db_sess.flush()
        return resource_group_names

    @pytest.fixture
    async def sample_scaling_groups_small(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[list[str], None]:
        """Create 5 sample scaling groups for basic testing"""
        yield await self._create_scaling_groups(db_with_cleanup, 5)

    @pytest.fixture
    async def sample_scaling_groups_for_pagination(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[list[str], None]:
        """Create 25 sample scaling groups for pagination testing"""
        yield await self._create_scaling_groups(db_with_cleanup, 25)

    @pytest.fixture
    async def sample_scaling_groups_mixed_active(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[list[str], None]:
        """Create 20 sample scaling groups (10 active, 10 inactive) for filter testing"""
        yield await self._create_scaling_groups(
            db_with_cleanup, 20, is_active_func=lambda i: i % 2 == 0
        )

    @pytest.fixture
    async def sample_scaling_groups_medium(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[list[str], None]:
        """Create 15 sample scaling groups for no-pagination testing"""
        yield await self._create_scaling_groups(db_with_cleanup, 15)

    @pytest.fixture
    async def sample_scaling_group_for_update(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[str, None]:
        """Create a single scaling group for update testing"""
        sgroup_name = f"{uuid.uuid4()}"
        async with db_with_cleanup.begin_session() as db_sess:
            sgroup = ResourceGroupRow(
                name=sgroup_name,
                description="Test scaling group for update",
                is_active=True,
                is_public=True,
                created_at=datetime.now(tz=UTC),
                wsproxy_addr=None,
                wsproxy_api_token=None,
                driver="static",
                driver_opts={},
                scheduler="fifo",
                scheduler_opts=ResourceGroupOpts(),
                use_host_network=False,
            )
            db_sess.add(sgroup)
            await db_sess.flush()
        yield sgroup_name

    @pytest.fixture
    async def sample_scaling_group_for_purge(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[tuple[ResourceGroupID, str], None]:
        """Create a single scaling group for purge testing"""
        sgroup_id = ResourceGroupID(uuid.uuid4())
        sgroup_name = f"{uuid.uuid4()}"
        async with db_with_cleanup.begin_session() as db_sess:
            sgroup = ResourceGroupRow(
                id=sgroup_id,
                name=sgroup_name,
                description="Test scaling group for purge",
                is_active=True,
                is_public=True,
                created_at=datetime.now(tz=UTC),
                wsproxy_addr=None,
                wsproxy_api_token=None,
                driver="static",
                driver_opts={},
                scheduler="fifo",
                scheduler_opts=ResourceGroupOpts(),
                use_host_network=False,
            )
            db_sess.add(sgroup)
            await db_sess.flush()
        yield sgroup_id, sgroup_name

    @pytest.fixture
    async def resource_group_for_update(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[str, None]:
        """Create a single scaling group for update testing"""
        sgroup_name = f"test-sgroup-update-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as db_sess:
            sgroup = ResourceGroupRow(
                name=sgroup_name,
                description="Test scaling group for update",
                is_active=True,
                is_public=True,
                created_at=datetime.now(tz=UTC),
                wsproxy_addr=None,
                wsproxy_api_token=None,
                driver="static",
                driver_opts={},
                scheduler="fifo",
                scheduler_opts=ResourceGroupOpts(),
                use_host_network=False,
            )
            db_sess.add(sgroup)
            await db_sess.flush()
        yield sgroup_name

    @pytest.fixture
    async def test_user_domain_group(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[tuple[uuid.UUID, str, uuid.UUID], None]:
        """Create test user, domain, and group for cascade delete testing.

        Returns:
            Tuple of (user_uuid, domain_name, group_id)
        """
        domain_id = DomainID(uuid.uuid4())
        test_user_uuid = uuid.uuid4()
        test_domain = f"test-domain-{uuid.uuid4().hex[:8]}"
        test_group_id = uuid.uuid4()
        test_resource_policy = f"test-policy-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            # Create domain
            domain = DomainRow(
                id=domain_id,
                name=test_domain,
                description="Test domain for cascade delete",
                is_active=True,
                total_resource_slots=ResourceSlot(),
            )
            db_sess.add(domain)

            # Create user resource policy
            user_resource_policy = UserResourcePolicyRow(
                name=test_resource_policy,
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_session_count_per_model_session=10,
                max_customized_image_count=10,
            )
            db_sess.add(user_resource_policy)

            # Create project resource policy
            project_resource_policy = ProjectResourcePolicyRow(
                name=test_resource_policy,
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_network_count=3,
            )
            db_sess.add(project_resource_policy)

            # Create user
            test_user_email = f"test-{uuid.uuid4().hex[:8]}@example.com"
            user = UserRow(
                uuid=test_user_uuid,
                username=f"test-user-{uuid.uuid4().hex[:8]}",
                email=test_user_email,
                password=PasswordInfo(
                    password="test_password",
                    algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
                    rounds=100_000,
                    salt_size=32,
                ),
                domain_id=domain_id,
                need_password_change=False,
                status=UserStatus.ACTIVE,
                status_info="active",
                created_at=datetime.now(tz=UTC),
                domain_name=test_domain,
                resource_policy=test_resource_policy,
            )
            db_sess.add(user)

            # Create group
            group = ProjectRow(
                id=test_group_id,
                name=f"test-group-{uuid.uuid4().hex[:8]}",
                description="Test group for cascade delete",
                is_active=True,
                created_at=datetime.now(tz=UTC),
                domain_name=test_domain,
                total_resource_slots=ResourceSlot(),
                allowed_vfolder_hosts={},
                resource_policy=test_resource_policy,
            )
            db_sess.add(group)

            await db_sess.flush()

        yield (test_user_uuid, test_domain, test_group_id)

    @pytest.fixture
    async def resource_group_repository(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ResourceGroupRepository, None]:
        """Create ResourceGroupRepository instance with database"""
        repo = ResourceGroupRepository(db_with_cleanup, V2DBOpsProvider(db_with_cleanup))
        yield repo

    @pytest.fixture
    async def sample_domain(
        self,
        domain_factory: DomainFactory,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> DomainFixtureData:
        """Create a sample domain for testing"""
        return await domain_factory(db_with_cleanup, name="test-domain-for-sgroup")

    @pytest.fixture
    async def sample_scaling_group_for_association(
        self,
        resource_group_repository: ResourceGroupRepository,
    ) -> AsyncGenerator[tuple[ResourceGroupID, str], None]:
        """Create a sample scaling group for association testing"""
        sgroup_name = "test-sgroup-associate-domain"
        creator = self._create_scaling_group_creator(
            name=sgroup_name,
            description="Test scaling group for association",
        )
        created = await resource_group_repository.create_resource_group(creator)

        yield created.id, sgroup_name

    async def test_search_scaling_groups_all(
        self,
        resource_group_repository: ResourceGroupRepository,
        sample_scaling_groups_small: list[str],
    ) -> None:
        """Test searching all scaling groups without filters"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=1000, offset=0),
            conditions=[],
            orders=[],
        )
        result = await resource_group_repository.search_resource_groups(querier=querier)

        # Should have exactly 5 test scaling groups
        assert len(result.items) == 5
        assert result.total_count == 5

        # Verify test scaling groups are in results
        result_names = {sg.name for sg in result.items}
        for test_sg_name in sample_scaling_groups_small:
            assert test_sg_name in result_names

    async def test_search_scaling_groups_with_querier(
        self,
        resource_group_repository: ResourceGroupRepository,
        sample_scaling_groups_small: list[str],
    ) -> None:
        """Test searching scaling groups with querier"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=100, offset=0),
            conditions=[],
            orders=[],
        )
        result = await resource_group_repository.search_resource_groups(querier=querier)

        assert len(result.items) == 5
        assert result.total_count == 5

    # Pagination Tests

    @pytest.mark.parametrize(
        "limit,offset,expected_items,total_count,description",
        [
            (10, 0, 10, 25, "first page"),
            (10, 10, 10, 25, "second page"),
            (10, 20, 5, 25, "last page with partial results"),
        ],
        ids=["first_page", "second_page", "last_page"],
    )
    async def test_search_scaling_groups_offset_pagination(
        self,
        resource_group_repository: ResourceGroupRepository,
        sample_scaling_groups_for_pagination: list[str],
        limit: int,
        offset: int,
        expected_items: int,
        total_count: int,
        description: str,
    ) -> None:
        """Test offset-based pagination scenarios"""
        querier = BatchQuerier(
            conditions=[],
            orders=[],
            pagination=OffsetPagination(limit=limit, offset=offset),
        )
        result = await resource_group_repository.search_resource_groups(querier=querier)

        assert len(result.items) == expected_items
        assert result.total_count == total_count

    @pytest.mark.parametrize(
        "limit,offset,expected_items,total_count,description",
        [
            (100, 0, 5, 5, "limit exceeds total count"),
            (10, 10000, 0, 5, "offset exceeds total count"),
        ],
        ids=["limit_exceeds", "offset_exceeds"],
    )
    async def test_search_scaling_groups_pagination_edge_cases(
        self,
        resource_group_repository: ResourceGroupRepository,
        sample_scaling_groups_small: list[str],
        limit: int,
        offset: int,
        expected_items: int,
        total_count: int,
        description: str,
    ) -> None:
        """Test pagination edge cases"""
        querier = BatchQuerier(
            conditions=[],
            orders=[],
            pagination=OffsetPagination(limit=limit, offset=offset),
        )
        result = await resource_group_repository.search_resource_groups(querier=querier)

        assert len(result.items) == expected_items
        assert result.total_count == total_count

    async def test_search_scaling_groups_large_limit(
        self,
        resource_group_repository: ResourceGroupRepository,
        sample_scaling_groups_medium: list[str],
    ) -> None:
        """Test searching scaling groups with large limit returns all items"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=1000, offset=0),
            conditions=[],
            orders=[],
        )
        result = await resource_group_repository.search_resource_groups(querier=querier)

        # Should have exactly 15 test scaling groups
        assert len(result.items) == 15
        assert result.total_count == 15

    # Create Tests

    async def test_create_scaling_group_success(
        self,
        resource_group_repository: ResourceGroupRepository,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> None:
        """Test creating a scaling group with all fields specified"""
        scheduler_opts = ResourceGroupOpts(
            allowed_session_types=[SessionTypes.INTERACTIVE],
            config={"max_sessions": 10},
        )
        creator = self._create_scaling_group_creator(
            name="test-sgroup-create-full",
            driver="docker",
            scheduler="fifo",
            description="Full test scaling group",
            is_active=True,
            is_public=False,
            wsproxy_addr="http://wsproxy:5000",
            wsproxy_api_token="test-token",
            driver_opts={"docker_host": "unix:///var/run/docker.sock"},
            scheduler_opts=scheduler_opts,
            use_host_network=True,
        )
        result = await resource_group_repository.create_resource_group(creator)

        assert result.name == "test-sgroup-create-full"
        assert result.driver.name == "docker"
        assert result.driver.options == {"docker_host": "unix:///var/run/docker.sock"}
        assert result.metadata.description == "Full test scaling group"
        assert result.status.is_public is False
        assert result.network.wsproxy_addr == "http://wsproxy:5000"
        assert result.network.wsproxy_api_token == "test-token"
        assert result.network.use_host_network is True

    async def test_create_scaling_group_duplicate_name_raises_conflict(
        self,
        resource_group_repository: ResourceGroupRepository,
    ) -> None:
        """Test creating a scaling group with duplicate name raises ScalingGroupConflict"""
        creator = self._create_scaling_group_creator(name=f"{uuid.uuid4()}")

        # First creation should succeed
        await resource_group_repository.create_resource_group(creator)

        # Second creation with same name should raise conflict
        with pytest.raises(ResourceGroupConflict):
            await resource_group_repository.create_resource_group(creator)

    # Update Tests

    async def test_update_scaling_group_success(
        self,
        resource_group_repository: ResourceGroupRepository,
        sample_scaling_group_for_update: str,
    ) -> None:
        """Test updating a scaling group"""
        new_scheduler_opts = ResourceGroupOpts(
            allowed_session_types=[SessionTypes.BATCH],
        )
        updater = ResourceGroupUpdater(
            resource_group_id=await resource_group_repository.get_resource_group_id_by_name(
                ResourceGroupName(sample_scaling_group_for_update)
            ),
            is_active=OptionalState.update(False),
            is_public=OptionalState.update(False),
            description=TriState.update("Updated description"),
            wsproxy_addr=TriState.update("http://new-wsproxy:5000"),
            wsproxy_api_token=TriState.update("new-token"),
            use_host_network=OptionalState.update(True),
            driver=OptionalState.update("docker"),
            driver_opts=OptionalState.update({"new_opt": "value"}),
            scheduler=OptionalState.update("drf"),
            scheduler_opts=OptionalState.update(new_scheduler_opts),
        )
        result = await resource_group_repository.update_resource_group(updater)

        assert result.metadata.description == "Updated description"
        assert result.status.is_active is False
        assert result.status.is_public is False
        assert result.network.wsproxy_addr == "http://new-wsproxy:5000"
        assert result.network.wsproxy_api_token == "new-token"
        assert result.driver.name == "docker"
        assert result.driver.options == {"new_opt": "value"}
        assert result.scheduler.name.value == "drf"
        assert SessionTypes.BATCH in result.scheduler.options.allowed_session_types
        assert result.network.use_host_network is True

    async def test_update_preemption_victim_scope_round_trips(
        self,
        resource_group_repository: ResourceGroupRepository,
        sample_scaling_group_for_update: str,
    ) -> None:
        """A preemption-config update persists ``victim_scope`` and the
        re-read data reflects it."""
        updater = ResourceGroupUpdater(
            resource_group_id=await resource_group_repository.get_resource_group_id_by_name(
                ResourceGroupName(sample_scaling_group_for_update)
            ),
            preemption_config=OptionalState.update(
                DataPreemptionConfig(
                    enabled=True,
                    victim_scope=PreemptionVictimScope.DOMAIN,
                )
            ),
        )
        result = await resource_group_repository.update_resource_group(updater)

        assert result.scheduler.options.preemption.enabled is True
        assert result.scheduler.options.preemption.victim_scope == PreemptionVictimScope.DOMAIN

    async def test_update_scaling_group_not_found(
        self,
        resource_group_repository: ResourceGroupRepository,
    ) -> None:
        """Test updating a non-existent scaling group raises ScalingGroupNotFound"""
        with pytest.raises(ResourceGroupNotFound):
            resource_group_id = await resource_group_repository.get_resource_group_id_by_name(
                ResourceGroupName("test-sgroup-nonexistent")
            )
            await resource_group_repository.update_resource_group(
                ResourceGroupUpdater(
                    resource_group_id=resource_group_id,
                    description=TriState.update("Updated description"),
                )
            )

    # Default Resource Group Tests

    @pytest.fixture
    async def existing_default_scaling_group(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[str, None]:
        """Create a scaling group that is already the default one"""
        sgroup_name = f"test-sgroup-default-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as db_sess:
            sgroup = ResourceGroupRow(
                name=sgroup_name,
                description="Existing default scaling group",
                is_active=True,
                is_public=True,
                is_default=True,
                created_at=datetime.now(tz=UTC),
                wsproxy_addr=None,
                wsproxy_api_token=None,
                driver="static",
                driver_opts={},
                scheduler="fifo",
                scheduler_opts=ResourceGroupOpts(),
                use_host_network=False,
            )
            db_sess.add(sgroup)
            await db_sess.flush()
        yield sgroup_name

    async def _default_scaling_group_names(
        self,
        db_engine: ExtendedAsyncSAEngine,
    ) -> list[str]:
        """Names of every scaling group currently flagged as the default"""
        async with db_engine.begin_readonly_session() as db_sess:
            result = await db_sess.execute(
                sa.select(ResourceGroupRow.name).where(ResourceGroupRow.is_default.is_(True))
            )
            return list(result.scalars())

    async def test_set_true_while_another_group_is_default_is_rejected(
        self,
        resource_group_repository: ResourceGroupRepository,
        db_with_cleanup: ExtendedAsyncSAEngine,
        existing_default_scaling_group: str,
        resource_group_for_update: str,
    ) -> None:
        """A second default is rejected as a bad request; the current one is untouched"""
        updater = ResourceGroupUpdater(
            resource_group_id=await resource_group_repository.get_resource_group_id_by_name(
                ResourceGroupName(resource_group_for_update)
            ),
            is_default=OptionalState.update(True),
        )

        with pytest.raises(DefaultResourceGroupAlreadyExists):
            await resource_group_repository.update_resource_group(updater)

        assert await self._default_scaling_group_names(db_with_cleanup) == [
            existing_default_scaling_group
        ]

    async def test_set_true_while_no_group_is_default_succeeds(
        self,
        resource_group_repository: ResourceGroupRepository,
        db_with_cleanup: ExtendedAsyncSAEngine,
        resource_group_for_update: str,
    ) -> None:
        """Setting the flag works while it is free"""
        updater = ResourceGroupUpdater(
            resource_group_id=await resource_group_repository.get_resource_group_id_by_name(
                ResourceGroupName(resource_group_for_update)
            ),
            is_default=OptionalState.update(True),
        )

        result = await resource_group_repository.update_resource_group(updater)

        assert result.status.is_default is True
        assert await self._default_scaling_group_names(db_with_cleanup) == [
            resource_group_for_update
        ]

    async def test_set_false_on_the_only_default_leaves_none(
        self,
        resource_group_repository: ResourceGroupRepository,
        db_with_cleanup: ExtendedAsyncSAEngine,
        existing_default_scaling_group: str,
    ) -> None:
        """Clearing the flag on the sole default is allowed and leaves no default behind"""
        updater = ResourceGroupUpdater(
            resource_group_id=await resource_group_repository.get_resource_group_id_by_name(
                ResourceGroupName(existing_default_scaling_group)
            ),
            is_default=OptionalState.update(False),
        )

        result = await resource_group_repository.update_resource_group(updater)

        assert result.status.is_default is False
        assert await self._default_scaling_group_names(db_with_cleanup) == []

    # Purge Tests

    async def test_purge_scaling_group_success(
        self,
        resource_group_repository: ResourceGroupRepository,
        sample_scaling_group_for_purge: tuple[ResourceGroupID, str],
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> None:
        """Test purging a scaling group without any sessions or routes"""
        # Given: A scaling group created by fixture
        _, sgroup_name = sample_scaling_group_for_purge

        # When: Purge the scaling group
        result = await resource_group_repository.purge_resource_group(
            await resource_group_repository.get_resource_group_id_by_name(
                ResourceGroupName(sgroup_name)
            )
        )

        # Then: Should return the deleted scaling group data
        assert result.name == sgroup_name

        # And: Scaling group should no longer exist in database
        async with db_with_cleanup.begin_readonly_session() as db_sess:
            query = sa.select(ResourceGroupRow).where(ResourceGroupRow.name == sgroup_name)
            db_result = await db_sess.execute(query)
            row = db_result.scalar_one_or_none()
            assert row is None

    async def test_purge_scaling_group_not_found(
        self,
        resource_group_repository: ResourceGroupRepository,
    ) -> None:
        """Test purging non-existent scaling group raises ScalingGroupNotFound"""
        # Given: A purger for non-existent scaling group with uuid-based name
        non_existent_name = ResourceGroupName(f"test-sgroup-nonexistent-{uuid.uuid4().hex[:8]}")

        # When/Then: Purging should raise ResourceGroupNotFound
        with pytest.raises(ResourceGroupNotFound):
            resource_group_id = await resource_group_repository.get_resource_group_id_by_name(
                non_existent_name
            )
            await resource_group_repository.purge_resource_group(resource_group_id)

    # Associate with Domain Tests
    async def test_associate_scaling_group_with_domains_success(
        self,
        resource_group_repository: ResourceGroupRepository,
        sample_scaling_group_for_association: tuple[ResourceGroupID, str],
        sample_domain: DomainFixtureData,
    ) -> None:
        """Test associating a scaling group with domains"""
        sgroup_id, _ = sample_scaling_group_for_association
        binder = RBACScopeBinder(
            pairs=[
                RBACScopeBindingPair(
                    spec=ResourceGroupForDomainCreatorSpec(
                        resource_group_id=sgroup_id,
                        domain_id=sample_domain.domain_id,
                    ),
                    entity_ref=RBACElementRef(
                        RBACElementType.RESOURCE_GROUP,
                        str(sgroup_id),
                    ),
                    scope_ref=RBACElementRef(
                        RBACElementType.DOMAIN,
                        str(sample_domain.domain_id),
                    ),
                )
            ]
        )
        await resource_group_repository.associate_resource_group_with_domains(binder)

        # Verify association using repository method
        association_exists = (
            await resource_group_repository.check_resource_group_domain_association_exists(
                resource_group_id=sgroup_id,
                domain_id=sample_domain.domain_id,
            )
        )
        assert association_exists is True

    @pytest.fixture
    async def sample_scaling_group_with_domain_association(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_scaling_group_for_association: tuple[ResourceGroupID, str],
        sample_domain: DomainFixtureData,
    ) -> AsyncGenerator[tuple[ResourceGroupID, str, str], None]:
        """Create a scaling group with a single domain association for testing"""
        sgroup_id, sgroup_name = sample_scaling_group_for_association
        async with db_with_cleanup.begin_session() as db_sess:
            association = ResourceGroupForDomainRow(
                resource_group_id=sgroup_id,
                domain_id=sample_domain.domain_id,
            )
            db_sess.add(association)

        yield sgroup_id, sgroup_name, sample_domain.domain_name

    # Disassociate with Domain Tests
    async def test_disassociate_scaling_group_with_domains_success(
        self,
        resource_group_repository: ResourceGroupRepository,
        sample_scaling_group_with_domain_association: tuple[ResourceGroupID, str, str],
        sample_domain: DomainFixtureData,
    ) -> None:
        """Test disassociating a scaling group from a domain"""
        resource_group_id, _, _ = sample_scaling_group_with_domain_association

        # Disassociate the scaling group from the domain
        unbinder = ResourceGroupDomainEntityUnbinder(
            resource_group_ids=[resource_group_id],
            domain_id=sample_domain.domain_id,
        )
        await resource_group_repository.disassociate_resource_group_with_domains(unbinder)

        # Verify association is removed
        association_exists = (
            await resource_group_repository.check_resource_group_domain_association_exists(
                resource_group_id=resource_group_id,
                domain_id=sample_domain.domain_id,
            )
        )
        assert association_exists is False

    async def test_disassociate_scaling_group_with_domains_nonexistent(
        self,
        resource_group_repository: ResourceGroupRepository,
        sample_scaling_group_for_association: tuple[ResourceGroupID, str],
        sample_domain: DomainFixtureData,
    ) -> None:
        """Test disassociating a non-existent association (should not raise error)"""
        sgroup_id, _ = sample_scaling_group_for_association
        # Disassociate without prior association should succeed without error
        unbinder = ResourceGroupDomainEntityUnbinder(
            resource_group_ids=[sgroup_id],
            domain_id=sample_domain.domain_id,
        )
        await resource_group_repository.disassociate_resource_group_with_domains(unbinder)

    # Multiple Domains Tests

    @pytest.fixture
    async def sample_multiple_domains(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        domain_factory: DomainFactory,
    ) -> list[DomainFixtureData]:
        """Create multiple sample domains for bulk testing"""
        return [
            await domain_factory(db_with_cleanup, name=f"test-domain-bulk-{i}") for i in range(3)
        ]

    @pytest.fixture
    async def sample_scaling_group_with_multiple_domain_associations(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_scaling_group_for_association: tuple[ResourceGroupID, str],
        sample_multiple_domains: list[DomainFixtureData],
    ) -> AsyncGenerator[tuple[ResourceGroupID, str, list[DomainFixtureData]], None]:
        """Create a scaling group with multiple domain associations for testing"""
        sgroup_id, sgroup_name = sample_scaling_group_for_association
        async with db_with_cleanup.begin_session() as db_sess:
            for domain in sample_multiple_domains:
                association = ResourceGroupForDomainRow(
                    resource_group_id=sgroup_id,
                    domain_id=domain.domain_id,
                )
                db_sess.add(association)

        yield sgroup_id, sgroup_name, sample_multiple_domains

    async def test_associate_scaling_group_with_multiple_domains(
        self,
        resource_group_repository: ResourceGroupRepository,
        sample_scaling_group_for_association: tuple[ResourceGroupID, str],
        sample_multiple_domains: list[DomainFixtureData],
    ) -> None:
        """Test associating a scaling group with multiple domains at once"""
        sgroup_id, _ = sample_scaling_group_for_association
        binder = RBACScopeBinder(
            pairs=[
                RBACScopeBindingPair(
                    spec=ResourceGroupForDomainCreatorSpec(
                        resource_group_id=sgroup_id,
                        domain_id=domain.domain_id,
                    ),
                    entity_ref=RBACElementRef(
                        RBACElementType.RESOURCE_GROUP,
                        str(sgroup_id),
                    ),
                    scope_ref=RBACElementRef(
                        RBACElementType.DOMAIN,
                        str(domain.domain_id),
                    ),
                )
                for domain in sample_multiple_domains
            ]
        )
        await resource_group_repository.associate_resource_group_with_domains(binder)

        # Verify all associations exist
        for domain in sample_multiple_domains:
            association_exists = (
                await resource_group_repository.check_resource_group_domain_association_exists(
                    resource_group_id=sgroup_id,
                    domain_id=domain.domain_id,
                )
            )
            assert association_exists is True

    async def test_disassociate_scaling_group_with_multiple_domains(
        self,
        resource_group_repository: ResourceGroupRepository,
        sample_scaling_group_with_multiple_domain_associations: tuple[
            ResourceGroupID, str, list[DomainFixtureData]
        ],
    ) -> None:
        """Test disassociating a scaling group from multiple domains"""
        (
            resource_group_id,
            _,
            domains,
        ) = sample_scaling_group_with_multiple_domain_associations

        # Disassociate all domains one by one
        for domain in domains:
            unbinder = ResourceGroupDomainEntityUnbinder(
                resource_group_ids=[resource_group_id],
                domain_id=domain.domain_id,
            )
            await resource_group_repository.disassociate_resource_group_with_domains(unbinder)

        # Verify all associations are removed
        for domain in domains:
            association_exists = (
                await resource_group_repository.check_resource_group_domain_association_exists(
                    resource_group_id=resource_group_id,
                    domain_id=domain.domain_id,
                )
            )
            assert association_exists is False

    # Associate/Disassociate with Keypair Tests

    @pytest.fixture
    async def sample_keypair(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_user_domain_group: tuple[uuid.UUID, str, uuid.UUID],
    ) -> AsyncGenerator[AccessKey, None]:
        """Create a test keypair for association testing.

        Returns:
            The access_key of the created keypair.
        """
        test_user_uuid, _, _ = test_user_domain_group
        # access_key column is varchar(20), so we need to keep it short
        access_key = AccessKey(f"AK{uuid.uuid4().hex[:18].upper()}")
        keypair_policy_name = f"test-kp-policy-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            # Create keypair resource policy first
            keypair_policy = KeyPairResourcePolicyRow(
                name=keypair_policy_name,
                default_for_unspecified=DefaultForUnspecified.UNLIMITED,
                total_resource_slots=ResourceSlot(),
                max_session_lifetime=0,
                max_concurrent_sessions=30,
                max_pending_session_count=None,
                max_pending_session_resource_slots=None,
                max_concurrent_sftp_sessions=1,
                max_containers_per_session=1,
                idle_timeout=0,
                allowed_vfolder_hosts={},
            )
            db_sess.add(keypair_policy)

            keypair = KeyPairRow(
                user=test_user_uuid,
                access_key=access_key,
                secret_key=SecretValue(f"SK{uuid.uuid4().hex}"),
                is_active=True,
                is_admin=False,
                resource_policy=keypair_policy_name,
                rate_limit=1000,
                num_queries=0,
                ssh_public_key=None,
            )
            db_sess.add(keypair)
            await db_sess.flush()

        yield access_key

    async def test_associate_scaling_group_with_keypairs_success(
        self,
        resource_group_repository: ResourceGroupRepository,
        sample_scaling_group_for_purge: tuple[ResourceGroupID, str],
        sample_keypair: AccessKey,
    ) -> None:
        """Test associating a scaling group with keypairs."""
        # Given: A scaling group and a keypair
        sgroup_id, _ = sample_scaling_group_for_purge
        access_key = sample_keypair

        # When: Associate the scaling group with the keypair
        bulk_creator = BulkCreator(
            specs=[
                ResourceGroupForKeypairsCreatorSpec(
                    resource_group_id=sgroup_id,
                    access_key=access_key,
                )
            ]
        )
        await resource_group_repository.associate_resource_group_with_keypairs(bulk_creator)

        # Then: Association should exist
        association_exists = (
            await resource_group_repository.check_resource_group_keypair_association_exists(
                sgroup_id, access_key
            )
        )
        assert association_exists is True

    async def test_disassociate_scaling_group_with_keypairs_success(
        self,
        resource_group_repository: ResourceGroupRepository,
        sample_scaling_group_for_purge: tuple[ResourceGroupID, str],
        sample_keypair: AccessKey,
    ) -> None:
        """Test disassociating a scaling group from keypairs."""
        # Given: A scaling group associated with a keypair
        sgroup_id, _ = sample_scaling_group_for_purge
        access_key = sample_keypair

        # First, associate the scaling group with the keypair using repository
        bulk_creator = BulkCreator(
            specs=[
                ResourceGroupForKeypairsCreatorSpec(
                    resource_group_id=sgroup_id,
                    access_key=access_key,
                )
            ]
        )
        await resource_group_repository.associate_resource_group_with_keypairs(bulk_creator)

        # Verify association exists
        association_exists = (
            await resource_group_repository.check_resource_group_keypair_association_exists(
                sgroup_id, access_key
            )
        )
        assert association_exists is True

        # When: Disassociate the scaling group from the keypair
        purger = create_resource_group_for_keypairs_purger(
            resource_group_id=sgroup_id,
            access_key=access_key,
        )
        await resource_group_repository.disassociate_resource_group_with_keypairs(purger)

        # Then: Association should no longer exist
        association_exists = (
            await resource_group_repository.check_resource_group_keypair_association_exists(
                sgroup_id, access_key
            )
        )
        assert association_exists is False

    async def test_disassociate_nonexistent_scaling_group_with_keypairs(
        self,
        resource_group_repository: ResourceGroupRepository,
        sample_scaling_group_for_purge: tuple[ResourceGroupID, str],
        sample_keypair: AccessKey,
    ) -> None:
        """Test disassociating a non-existent association does not raise error."""
        # Given: A scaling group that is NOT associated with a keypair
        sgroup_id, _ = sample_scaling_group_for_purge
        access_key = sample_keypair

        # When: Disassociate (even though no association exists)
        purger = create_resource_group_for_keypairs_purger(
            resource_group_id=sgroup_id,
            access_key=access_key,
        )
        # Then: Should not raise any error (BatchPurger deletes 0 rows silently)
        await resource_group_repository.disassociate_resource_group_with_keypairs(purger)

    # Associate/Disassociate with User Group (Project) Tests

    async def test_associate_scaling_group_with_user_groups_success(
        self,
        resource_group_repository: ResourceGroupRepository,
        sample_scaling_group_for_purge: tuple[ResourceGroupID, str],
        test_user_domain_group: tuple[uuid.UUID, str, uuid.UUID],
    ) -> None:
        """Test associating a scaling group with user groups (projects)."""
        # Given: A scaling group and a project (group)
        sgroup_id, _ = sample_scaling_group_for_purge
        _, _, project_id = test_user_domain_group

        # When: Associate the scaling group with the project
        binder = RBACScopeBinder(
            pairs=[
                RBACScopeBindingPair(
                    spec=ResourceGroupForProjectCreatorSpec(
                        resource_group_id=sgroup_id,
                        project=project_id,
                    ),
                    entity_ref=RBACElementRef(
                        RBACElementType.RESOURCE_GROUP,
                        str(sgroup_id),
                    ),
                    scope_ref=RBACElementRef(
                        RBACElementType.PROJECT,
                        str(project_id),
                    ),
                )
            ]
        )
        await resource_group_repository.associate_resource_group_with_user_groups(binder)

        # Then: Association should exist
        association_exists = (
            await resource_group_repository.check_resource_group_user_group_association_exists(
                resource_group_id=sgroup_id,
                user_group=project_id,
            )
        )
        assert association_exists is True

    async def test_disassociate_scaling_group_with_user_groups_success(
        self,
        resource_group_repository: ResourceGroupRepository,
        sample_scaling_group_for_purge: tuple[ResourceGroupID, str],
        test_user_domain_group: tuple[uuid.UUID, str, uuid.UUID],
    ) -> None:
        """Test disassociating a scaling group from a user group (project)."""
        # Given: A scaling group associated with a project
        sgroup_id, _ = sample_scaling_group_for_purge
        _, _, project_id = test_user_domain_group

        # First, associate the scaling group with the project using repository
        binder = RBACScopeBinder(
            pairs=[
                RBACScopeBindingPair(
                    spec=ResourceGroupForProjectCreatorSpec(
                        resource_group_id=sgroup_id,
                        project=project_id,
                    ),
                    entity_ref=RBACElementRef(
                        RBACElementType.RESOURCE_GROUP,
                        str(sgroup_id),
                    ),
                    scope_ref=RBACElementRef(
                        RBACElementType.PROJECT,
                        str(project_id),
                    ),
                )
            ]
        )
        await resource_group_repository.associate_resource_group_with_user_groups(binder)

        # Verify association exists
        association_exists = (
            await resource_group_repository.check_resource_group_user_group_association_exists(
                resource_group_id=sgroup_id,
                user_group=project_id,
            )
        )
        assert association_exists is True

        # When: Disassociate the scaling group from the project
        unbinder = ResourceGroupProjectEntityUnbinder(
            resource_group_ids=[sgroup_id], project=project_id
        )
        await resource_group_repository.disassociate_resource_group_with_user_groups(unbinder)

        # Then: Association should no longer exist
        association_exists = (
            await resource_group_repository.check_resource_group_user_group_association_exists(
                resource_group_id=sgroup_id,
                user_group=project_id,
            )
        )
        assert association_exists is False

    async def test_disassociate_nonexistent_scaling_group_with_user_groups(
        self,
        resource_group_repository: ResourceGroupRepository,
        sample_scaling_group_for_purge: tuple[ResourceGroupID, str],
        test_user_domain_group: tuple[uuid.UUID, str, uuid.UUID],
    ) -> None:
        """Test disassociating a non-existent association does not raise error."""
        # Given: A scaling group that is NOT associated with a project
        sgroup_id, _ = sample_scaling_group_for_purge
        _, _, project_id = test_user_domain_group

        # When: Disassociate (even though no association exists)
        unbinder = ResourceGroupProjectEntityUnbinder(
            resource_group_ids=[sgroup_id], project=project_id
        )
        # Then: Should not raise any error (unbinder deletes 0 rows silently)
        await resource_group_repository.disassociate_resource_group_with_user_groups(unbinder)

    async def test_get_resource_group_id_by_name_success(
        self,
        resource_group_repository: ResourceGroupRepository,
        sample_scaling_groups_small: list[str],
    ) -> None:
        target_name = sample_scaling_groups_small[0]
        resource_group_id = await resource_group_repository.get_resource_group_id_by_name(
            ResourceGroupName(target_name)
        )
        fetched = await resource_group_repository.get_resource_group_by_name(target_name)
        assert resource_group_id == fetched.id

    async def test_get_resource_group_id_by_name_not_found(
        self,
        resource_group_repository: ResourceGroupRepository,
    ) -> None:
        with pytest.raises(ResourceGroupNotFound):
            await resource_group_repository.get_resource_group_id_by_name(
                ResourceGroupName("nonexistent-scaling-group")
            )
