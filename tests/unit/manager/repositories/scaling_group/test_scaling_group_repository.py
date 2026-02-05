import uuid
from collections.abc import AsyncGenerator, Callable
from datetime import UTC, datetime
from typing import Any

import pytest
import sqlalchemy as sa

from ai.backend.common.exception import ScalingGroupConflict
from ai.backend.common.types import AccessKey, DefaultForUnspecified, ResourceSlot, SessionTypes
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.user.types import UserStatus
from ai.backend.manager.defs import DEFAULT_ROLE
from ai.backend.manager.errors.resource import ScalingGroupNotFound
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.deployment_auto_scaling_policy import DeploymentAutoScalingPolicyRow
from ai.backend.manager.models.deployment_policy import DeploymentPolicyRow
from ai.backend.manager.models.deployment_revision import DeploymentRevisionRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.endpoint import EndpointLifecycle, EndpointRow
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.rbac_models import UserRoleRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.resource_preset import ResourcePresetRow
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.models.scaling_group import (
    ScalingGroupForDomainRow,
    ScalingGroupForKeypairsRow,
    ScalingGroupForProjectRow,
    ScalingGroupOpts,
    ScalingGroupRow,
)
from ai.backend.manager.models.session import SessionId, SessionRow
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import VFolderRow
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.manager.repositories.base.creator import BulkCreator, Creator
from ai.backend.manager.repositories.base.purger import Purger
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.scaling_group import ScalingGroupRepository
from ai.backend.manager.repositories.scaling_group.creators import (
    ScalingGroupCreatorSpec,
    ScalingGroupForDomainCreatorSpec,
    ScalingGroupForKeypairsCreatorSpec,
    ScalingGroupForProjectCreatorSpec,
)
from ai.backend.manager.repositories.scaling_group.purgers import (
    create_scaling_group_for_domain_purger,
    create_scaling_group_for_keypairs_purger,
    create_scaling_group_for_project_purger,
)
from ai.backend.manager.repositories.scaling_group.updaters import (
    ScalingGroupDriverConfigUpdaterSpec,
    ScalingGroupMetadataUpdaterSpec,
    ScalingGroupNetworkConfigUpdaterSpec,
    ScalingGroupSchedulerConfigUpdaterSpec,
    ScalingGroupStatusUpdaterSpec,
    ScalingGroupUpdaterSpec,
)
from ai.backend.manager.types import OptionalState, TriState
from ai.backend.testutils.db import with_tables


class TestScalingGroupRepositoryDB:
    """Test cases for ScalingGroupRepository"""

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
                ScalingGroupRow,
                ScalingGroupForDomainRow,
                ScalingGroupForProjectRow,
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                KeyPairResourcePolicyRow,
                UserRoleRow,
                UserRow,
                KeyPairRow,
                ScalingGroupForKeypairsRow,  # depends on ScalingGroupRow and KeyPairRow
                GroupRow,
                ImageRow,
                VFolderRow,
                EndpointRow,
                DeploymentPolicyRow,
                DeploymentAutoScalingPolicyRow,
                DeploymentRevisionRow,
                SessionRow,
                AgentRow,
                KernelRow,
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
        wsproxy_addr: str | None = None,
        wsproxy_api_token: str | None = None,
        driver_opts: dict[str, Any] | None = None,
        scheduler_opts: ScalingGroupOpts | None = None,
        use_host_network: bool = False,
    ) -> Creator[ScalingGroupRow]:
        """Create a ScalingGroupCreatorSpec with the given parameters."""
        spec = ScalingGroupCreatorSpec(
            name=name,
            driver=driver,
            scheduler=scheduler,
            description=description,
            is_active=is_active,
            is_public=is_public,
            wsproxy_addr=wsproxy_addr,
            wsproxy_api_token=wsproxy_api_token,
            driver_opts=driver_opts if driver_opts is not None else {},
            scheduler_opts=scheduler_opts,
            use_host_network=use_host_network,
        )
        return Creator(spec=spec)

    async def _create_scaling_groups(
        self,
        db_engine: ExtendedAsyncSAEngine,
        count: int,
        is_active_func: Callable[[int], bool] = lambda i: True,
    ) -> list[str]:
        """Helper to create scaling groups with given parameters"""
        scaling_group_names = []
        async with db_engine.begin_session() as db_sess:
            for i in range(count):
                sgroup_name = f"{uuid.uuid4()}"
                sgroup = ScalingGroupRow(
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
                    scheduler_opts=ScalingGroupOpts(),
                    use_host_network=False,
                )
                db_sess.add(sgroup)
                scaling_group_names.append(sgroup_name)
            await db_sess.flush()
        return scaling_group_names

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
            sgroup = ScalingGroupRow(
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
                scheduler_opts=ScalingGroupOpts(),
                use_host_network=False,
            )
            db_sess.add(sgroup)
            await db_sess.flush()
        yield sgroup_name

    @pytest.fixture
    async def sample_scaling_group_for_purge(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[str, None]:
        """Create a single scaling group for purge testing"""
        sgroup_name = f"{uuid.uuid4()}"
        async with db_with_cleanup.begin_session() as db_sess:
            sgroup = ScalingGroupRow(
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
                scheduler_opts=ScalingGroupOpts(),
                use_host_network=False,
            )
            db_sess.add(sgroup)
            await db_sess.flush()
        yield sgroup_name

    @pytest.fixture
    async def scaling_group_for_update(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[str, None]:
        """Create a single scaling group for update testing"""
        sgroup_name = f"test-sgroup-update-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as db_sess:
            sgroup = ScalingGroupRow(
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
                scheduler_opts=ScalingGroupOpts(),
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
        test_user_uuid = uuid.uuid4()
        test_domain = f"test-domain-{uuid.uuid4().hex[:8]}"
        test_group_id = uuid.uuid4()
        test_resource_policy = f"test-policy-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            # Create domain
            domain = DomainRow(
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
            user = UserRow(
                uuid=test_user_uuid,
                username=f"test-user-{uuid.uuid4().hex[:8]}",
                email=f"test-{uuid.uuid4().hex[:8]}@example.com",
                password=PasswordInfo(
                    password="test_password",
                    algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
                    rounds=100_000,
                    salt_size=32,
                ),
                need_password_change=False,
                status=UserStatus.ACTIVE,
                status_info="active",
                created_at=datetime.now(tz=UTC),
                domain_name=test_domain,
                resource_policy=test_resource_policy,
            )
            db_sess.add(user)

            # Create group
            group = GroupRow(
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
    async def sample_scaling_group_with_sessions_and_routes(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_user_domain_group: tuple[uuid.UUID, str, uuid.UUID],
    ) -> AsyncGenerator[str, None]:
        """Create scaling group with sessions and routes for cascade delete testing.

        Returns:
            The scaling group name
        """
        test_user_uuid, test_domain, test_group_id = test_user_domain_group
        sgroup_name = f"test-sgroup-cascade-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            # Create scaling group
            sgroup = ScalingGroupRow(
                name=sgroup_name,
                description="Test scaling group for cascade delete",
                is_active=True,
                is_public=True,
                created_at=datetime.now(tz=UTC),
                wsproxy_addr=None,
                wsproxy_api_token=None,
                driver="static",
                driver_opts={},
                scheduler="fifo",
                scheduler_opts=ScalingGroupOpts(),
                use_host_network=False,
            )
            db_sess.add(sgroup)
            await db_sess.flush()  # Flush to ensure scaling group exists before creating references

            # Create 2 sessions with this scaling group
            for i in range(2):
                session_id = SessionId(uuid.uuid4())
                session = SessionRow(
                    id=session_id,
                    domain_name=test_domain,
                    group_id=test_group_id,
                    user_uuid=test_user_uuid,
                    scaling_group_name=sgroup_name,
                    cluster_size=1,
                    vfolder_mounts={},
                )
                db_sess.add(session)

                # Create minimal endpoint for routing
                endpoint_id = uuid.uuid4()
                endpoint = EndpointRow(
                    id=endpoint_id,
                    name=f"test-endpoint-{i}",
                    domain=test_domain,
                    project=test_group_id,
                    resource_group=sgroup_name,
                    image=None,  # Allowed when lifecycle_stage=DESTROYED
                    lifecycle_stage=EndpointLifecycle.DESTROYED,
                    session_owner=test_user_uuid,
                    created_user=test_user_uuid,
                )
                db_sess.add(endpoint)

                # Create routing connected to session
                routing = RoutingRow(
                    id=uuid.uuid4(),
                    endpoint=endpoint_id,
                    session=session_id,
                    session_owner=test_user_uuid,
                    domain=test_domain,
                    project=test_group_id,
                    traffic_ratio=1.0,
                )
                db_sess.add(routing)

            await db_sess.flush()

        yield sgroup_name

    @pytest.fixture
    async def scaling_group_repository(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ScalingGroupRepository, None]:
        """Create ScalingGroupRepository instance with database"""
        repo = ScalingGroupRepository(
            db=db_with_cleanup,
        )
        yield repo

    @pytest.fixture
    async def sample_domain(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[str, None]:
        """Create a sample domain for testing"""
        domain_name = "test-domain-for-sgroup"
        async with db_with_cleanup.begin_session() as db_sess:
            domain = DomainRow(
                name=domain_name,
                description="Test domain",
                is_active=True,
                total_resource_slots=ResourceSlot(),
            )
            db_sess.add(domain)

        yield domain_name

    @pytest.fixture
    async def sample_scaling_group_for_association(
        self,
        scaling_group_repository: ScalingGroupRepository,
    ) -> AsyncGenerator[str, None]:
        """Create a sample scaling group for association testing"""
        sgroup_name = "test-sgroup-associate-domain"
        creator = self._create_scaling_group_creator(
            name=sgroup_name,
            description="Test scaling group for association",
        )
        await scaling_group_repository.create_scaling_group(creator)

        yield sgroup_name

    async def test_search_scaling_groups_all(
        self,
        scaling_group_repository: ScalingGroupRepository,
        sample_scaling_groups_small: list[str],
    ) -> None:
        """Test searching all scaling groups without filters"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=1000, offset=0),
            conditions=[],
            orders=[],
        )
        result = await scaling_group_repository.search_scaling_groups(querier=querier)

        # Should have exactly 5 test scaling groups
        assert len(result.items) == 5
        assert result.total_count == 5

        # Verify test scaling groups are in results
        result_names = {sg.name for sg in result.items}
        for test_sg_name in sample_scaling_groups_small:
            assert test_sg_name in result_names

    async def test_search_scaling_groups_with_querier(
        self,
        scaling_group_repository: ScalingGroupRepository,
        sample_scaling_groups_small: list[str],
    ) -> None:
        """Test searching scaling groups with querier"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=100, offset=0),
            conditions=[],
            orders=[],
        )
        result = await scaling_group_repository.search_scaling_groups(querier=querier)

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
        scaling_group_repository: ScalingGroupRepository,
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
        result = await scaling_group_repository.search_scaling_groups(querier=querier)

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
        scaling_group_repository: ScalingGroupRepository,
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
        result = await scaling_group_repository.search_scaling_groups(querier=querier)

        assert len(result.items) == expected_items
        assert result.total_count == total_count

    async def test_search_scaling_groups_large_limit(
        self,
        scaling_group_repository: ScalingGroupRepository,
        sample_scaling_groups_medium: list[str],
    ) -> None:
        """Test searching scaling groups with large limit returns all items"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=1000, offset=0),
            conditions=[],
            orders=[],
        )
        result = await scaling_group_repository.search_scaling_groups(querier=querier)

        # Should have exactly 15 test scaling groups
        assert len(result.items) == 15
        assert result.total_count == 15

    # Create Tests

    async def test_create_scaling_group_success(
        self,
        scaling_group_repository: ScalingGroupRepository,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> None:
        """Test creating a scaling group with all fields specified"""
        scheduler_opts = ScalingGroupOpts(
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
        result = await scaling_group_repository.create_scaling_group(creator)

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
        scaling_group_repository: ScalingGroupRepository,
    ) -> None:
        """Test creating a scaling group with duplicate name raises ScalingGroupConflict"""
        creator = self._create_scaling_group_creator(name=f"{uuid.uuid4()}")

        # First creation should succeed
        await scaling_group_repository.create_scaling_group(creator)

        # Second creation with same name should raise conflict
        with pytest.raises(ScalingGroupConflict):
            await scaling_group_repository.create_scaling_group(creator)

    # Update Tests

    async def test_update_scaling_group_success(
        self,
        scaling_group_repository: ScalingGroupRepository,
        sample_scaling_group_for_update: str,
    ) -> None:
        """Test updating a scaling group"""
        new_scheduler_opts = ScalingGroupOpts(
            allowed_session_types=[SessionTypes.BATCH],
        )
        spec = ScalingGroupUpdaterSpec(
            status=ScalingGroupStatusUpdaterSpec(
                is_active=OptionalState.update(False),
                is_public=OptionalState.update(False),
            ),
            metadata=ScalingGroupMetadataUpdaterSpec(
                description=TriState.update("Updated description"),
            ),
            network=ScalingGroupNetworkConfigUpdaterSpec(
                wsproxy_addr=TriState.update("http://new-wsproxy:5000"),
                wsproxy_api_token=TriState.update("new-token"),
                use_host_network=OptionalState.update(True),
            ),
            driver=ScalingGroupDriverConfigUpdaterSpec(
                driver=OptionalState.update("docker"),
                driver_opts=OptionalState.update({"new_opt": "value"}),
            ),
            scheduler=ScalingGroupSchedulerConfigUpdaterSpec(
                scheduler=OptionalState.update("drf"),
                scheduler_opts=OptionalState.update(new_scheduler_opts),
            ),
        )
        updater = Updater(spec=spec, pk_value=sample_scaling_group_for_update)
        result = await scaling_group_repository.update_scaling_group(updater)

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

    async def test_update_scaling_group_not_found(
        self,
        scaling_group_repository: ScalingGroupRepository,
    ) -> None:
        """Test updating a non-existent scaling group raises ScalingGroupNotFound"""
        spec = ScalingGroupUpdaterSpec(
            metadata=ScalingGroupMetadataUpdaterSpec(
                description=TriState.update("Updated description"),
            ),
        )
        updater = Updater(spec=spec, pk_value="test-sgroup-nonexistent")

        with pytest.raises(ScalingGroupNotFound):
            await scaling_group_repository.update_scaling_group(updater)

    # Purge Tests

    async def test_purge_scaling_group_success(
        self,
        scaling_group_repository: ScalingGroupRepository,
        sample_scaling_group_for_purge: str,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> None:
        """Test purging a scaling group without any sessions or routes"""
        # Given: A scaling group created by fixture
        sgroup_name = sample_scaling_group_for_purge

        # When: Purge the scaling group
        purger = Purger(row_class=ScalingGroupRow, pk_value=sgroup_name)
        result = await scaling_group_repository.purge_scaling_group(purger)

        # Then: Should return the deleted scaling group data
        assert result.name == sgroup_name

        # And: Scaling group should no longer exist in database
        async with db_with_cleanup.begin_readonly_session() as db_sess:
            query = sa.select(ScalingGroupRow).where(ScalingGroupRow.name == sgroup_name)
            db_result = await db_sess.execute(query)
            row = db_result.scalar_one_or_none()
            assert row is None

    async def test_purge_scaling_group_not_found(
        self,
        scaling_group_repository: ScalingGroupRepository,
    ) -> None:
        """Test purging non-existent scaling group raises ScalingGroupNotFound"""
        # Given: A purger for non-existent scaling group with uuid-based name
        non_existent_name = f"test-sgroup-nonexistent-{uuid.uuid4().hex[:8]}"
        purger = Purger(row_class=ScalingGroupRow, pk_value=non_existent_name)

        # When/Then: Purging should raise ScalingGroupNotFound
        with pytest.raises(ScalingGroupNotFound):
            await scaling_group_repository.purge_scaling_group(purger)

    async def test_purge_scaling_group_with_sessions_and_routes(
        self,
        scaling_group_repository: ScalingGroupRepository,
        sample_scaling_group_with_sessions_and_routes: str,
    ) -> None:
        """Test purging a scaling group with associated sessions and routes."""
        # Given: A scaling group with sessions and routes (created by fixture)
        sgroup_name = sample_scaling_group_with_sessions_and_routes

        # When: Purge the scaling group
        purger = Purger(row_class=ScalingGroupRow, pk_value=sgroup_name)
        result = await scaling_group_repository.purge_scaling_group(purger)

        # Then: Should return the deleted scaling group data
        assert result.name == sgroup_name
        assert result.metadata.description == "Test scaling group for cascade delete"

    # Associate with Domain Tests
    async def test_associate_scaling_group_with_domains_success(
        self,
        scaling_group_repository: ScalingGroupRepository,
        sample_scaling_group_for_association: str,
        sample_domain: str,
    ) -> None:
        """Test associating a scaling group with domains"""
        bulk_creator = BulkCreator(
            specs=[
                ScalingGroupForDomainCreatorSpec(
                    scaling_group=sample_scaling_group_for_association,
                    domain=sample_domain,
                )
            ]
        )
        await scaling_group_repository.associate_scaling_group_with_domains(bulk_creator)

        # Verify association using repository method
        association_exists = (
            await scaling_group_repository.check_scaling_group_domain_association_exists(
                scaling_group=sample_scaling_group_for_association,
                domain=sample_domain,
            )
        )
        assert association_exists is True

    @pytest.fixture
    async def sample_scaling_group_with_domain_association(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_scaling_group_for_association: str,
        sample_domain: str,
    ) -> AsyncGenerator[tuple[str, str], None]:
        """Create a scaling group with a single domain association for testing"""
        async with db_with_cleanup.begin_session() as db_sess:
            association = ScalingGroupForDomainRow(
                scaling_group=sample_scaling_group_for_association,
                domain=sample_domain,
            )
            db_sess.add(association)

        yield sample_scaling_group_for_association, sample_domain

    # Disassociate with Domain Tests
    async def test_disassociate_scaling_group_with_domains_success(
        self,
        scaling_group_repository: ScalingGroupRepository,
        sample_scaling_group_with_domain_association: tuple[str, str],
    ) -> None:
        """Test disassociating a scaling group from a domain"""
        scaling_group, domain = sample_scaling_group_with_domain_association

        # Disassociate the scaling group from the domain
        purger = create_scaling_group_for_domain_purger(
            scaling_group=scaling_group,
            domain=domain,
        )
        await scaling_group_repository.disassociate_scaling_group_with_domains(purger)

        # Verify association is removed
        association_exists = (
            await scaling_group_repository.check_scaling_group_domain_association_exists(
                scaling_group=scaling_group,
                domain=domain,
            )
        )
        assert association_exists is False

    async def test_disassociate_scaling_group_with_domains_nonexistent(
        self,
        scaling_group_repository: ScalingGroupRepository,
        sample_scaling_group_for_association: str,
        sample_domain: str,
    ) -> None:
        """Test disassociating a non-existent association (should not raise error)"""
        # Disassociate without prior association should succeed without error
        purger = create_scaling_group_for_domain_purger(
            scaling_group=sample_scaling_group_for_association,
            domain=sample_domain,
        )
        await scaling_group_repository.disassociate_scaling_group_with_domains(purger)

    # Multiple Domains Tests

    @pytest.fixture
    async def sample_multiple_domains(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[list[str], None]:
        """Create multiple sample domains for bulk testing"""
        domain_names = [f"test-domain-bulk-{i}" for i in range(3)]
        async with db_with_cleanup.begin_session() as db_sess:
            for domain_name in domain_names:
                domain = DomainRow(
                    name=domain_name,
                    description=f"Test domain {domain_name}",
                    is_active=True,
                    total_resource_slots=ResourceSlot(),
                )
                db_sess.add(domain)

        yield domain_names

    @pytest.fixture
    async def sample_scaling_group_with_multiple_domain_associations(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_scaling_group_for_association: str,
        sample_multiple_domains: list[str],
    ) -> AsyncGenerator[tuple[str, list[str]], None]:
        """Create a scaling group with multiple domain associations for testing"""
        async with db_with_cleanup.begin_session() as db_sess:
            for domain in sample_multiple_domains:
                association = ScalingGroupForDomainRow(
                    scaling_group=sample_scaling_group_for_association,
                    domain=domain,
                )
                db_sess.add(association)

        yield sample_scaling_group_for_association, sample_multiple_domains

    async def test_associate_scaling_group_with_multiple_domains(
        self,
        scaling_group_repository: ScalingGroupRepository,
        sample_scaling_group_for_association: str,
        sample_multiple_domains: list[str],
    ) -> None:
        """Test associating a scaling group with multiple domains at once"""
        bulk_creator = BulkCreator(
            specs=[
                ScalingGroupForDomainCreatorSpec(
                    scaling_group=sample_scaling_group_for_association,
                    domain=domain,
                )
                for domain in sample_multiple_domains
            ]
        )
        await scaling_group_repository.associate_scaling_group_with_domains(bulk_creator)

        # Verify all associations exist
        for domain in sample_multiple_domains:
            association_exists = (
                await scaling_group_repository.check_scaling_group_domain_association_exists(
                    scaling_group=sample_scaling_group_for_association,
                    domain=domain,
                )
            )
            assert association_exists is True

    async def test_disassociate_scaling_group_with_multiple_domains(
        self,
        scaling_group_repository: ScalingGroupRepository,
        sample_scaling_group_with_multiple_domain_associations: tuple[str, list[str]],
    ) -> None:
        """Test disassociating a scaling group from multiple domains"""
        scaling_group, domains = sample_scaling_group_with_multiple_domain_associations

        # Disassociate all domains one by one
        for domain in domains:
            purger = create_scaling_group_for_domain_purger(
                scaling_group=scaling_group,
                domain=domain,
            )
            await scaling_group_repository.disassociate_scaling_group_with_domains(purger)

        # Verify all associations are removed
        for domain in domains:
            association_exists = (
                await scaling_group_repository.check_scaling_group_domain_association_exists(
                    scaling_group=scaling_group,
                    domain=domain,
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
                secret_key=f"SK{uuid.uuid4().hex}",
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
        scaling_group_repository: ScalingGroupRepository,
        sample_scaling_group_for_purge: str,
        sample_keypair: AccessKey,
    ) -> None:
        """Test associating a scaling group with keypairs."""
        # Given: A scaling group and a keypair
        sgroup_name = sample_scaling_group_for_purge
        access_key = sample_keypair

        # When: Associate the scaling group with the keypair
        bulk_creator = BulkCreator(
            specs=[
                ScalingGroupForKeypairsCreatorSpec(
                    scaling_group=sgroup_name,
                    access_key=access_key,
                )
            ]
        )
        await scaling_group_repository.associate_scaling_group_with_keypairs(bulk_creator)

        # Then: Association should exist
        association_exists = (
            await scaling_group_repository.check_scaling_group_keypair_association_exists(
                sgroup_name, access_key
            )
        )
        assert association_exists is True

    async def test_disassociate_scaling_group_with_keypairs_success(
        self,
        scaling_group_repository: ScalingGroupRepository,
        sample_scaling_group_for_purge: str,
        sample_keypair: AccessKey,
    ) -> None:
        """Test disassociating a scaling group from keypairs."""
        # Given: A scaling group associated with a keypair
        sgroup_name = sample_scaling_group_for_purge
        access_key = sample_keypair

        # First, associate the scaling group with the keypair using repository
        bulk_creator = BulkCreator(
            specs=[
                ScalingGroupForKeypairsCreatorSpec(
                    scaling_group=sgroup_name,
                    access_key=access_key,
                )
            ]
        )
        await scaling_group_repository.associate_scaling_group_with_keypairs(bulk_creator)

        # Verify association exists
        association_exists = (
            await scaling_group_repository.check_scaling_group_keypair_association_exists(
                sgroup_name, access_key
            )
        )
        assert association_exists is True

        # When: Disassociate the scaling group from the keypair
        purger = create_scaling_group_for_keypairs_purger(
            scaling_group=sgroup_name,
            access_key=access_key,
        )
        await scaling_group_repository.disassociate_scaling_group_with_keypairs(purger)

        # Then: Association should no longer exist
        association_exists = (
            await scaling_group_repository.check_scaling_group_keypair_association_exists(
                sgroup_name, access_key
            )
        )
        assert association_exists is False

    async def test_disassociate_nonexistent_scaling_group_with_keypairs(
        self,
        scaling_group_repository: ScalingGroupRepository,
        sample_scaling_group_for_purge: str,
        sample_keypair: AccessKey,
    ) -> None:
        """Test disassociating a non-existent association does not raise error."""
        # Given: A scaling group that is NOT associated with a keypair
        sgroup_name = sample_scaling_group_for_purge
        access_key = sample_keypair

        # When: Disassociate (even though no association exists)
        purger = create_scaling_group_for_keypairs_purger(
            scaling_group=sgroup_name,
            access_key=access_key,
        )
        # Then: Should not raise any error (BatchPurger deletes 0 rows silently)
        await scaling_group_repository.disassociate_scaling_group_with_keypairs(purger)

    # Associate/Disassociate with User Group (Project) Tests

    async def test_associate_scaling_group_with_user_groups_success(
        self,
        scaling_group_repository: ScalingGroupRepository,
        sample_scaling_group_for_purge: str,
        test_user_domain_group: tuple[uuid.UUID, str, uuid.UUID],
    ) -> None:
        """Test associating a scaling group with user groups (projects)."""
        # Given: A scaling group and a project (group)
        sgroup_name = sample_scaling_group_for_purge
        _, _, project_id = test_user_domain_group

        # When: Associate the scaling group with the project
        bulk_creator = BulkCreator(
            specs=[
                ScalingGroupForProjectCreatorSpec(
                    scaling_group=sgroup_name,
                    project=project_id,
                )
            ]
        )
        await scaling_group_repository.associate_scaling_group_with_user_groups(bulk_creator)

        # Then: Association should exist
        association_exists = (
            await scaling_group_repository.check_scaling_group_user_group_association_exists(
                scaling_group=sgroup_name,
                user_group=project_id,
            )
        )
        assert association_exists is True

    async def test_disassociate_scaling_group_with_user_groups_success(
        self,
        scaling_group_repository: ScalingGroupRepository,
        sample_scaling_group_for_purge: str,
        test_user_domain_group: tuple[uuid.UUID, str, uuid.UUID],
    ) -> None:
        """Test disassociating a scaling group from a user group (project)."""
        # Given: A scaling group associated with a project
        sgroup_name = sample_scaling_group_for_purge
        _, _, project_id = test_user_domain_group

        # First, associate the scaling group with the project using repository
        bulk_creator = BulkCreator(
            specs=[
                ScalingGroupForProjectCreatorSpec(
                    scaling_group=sgroup_name,
                    project=project_id,
                )
            ]
        )
        await scaling_group_repository.associate_scaling_group_with_user_groups(bulk_creator)

        # Verify association exists
        association_exists = (
            await scaling_group_repository.check_scaling_group_user_group_association_exists(
                scaling_group=sgroup_name,
                user_group=project_id,
            )
        )
        assert association_exists is True

        # When: Disassociate the scaling group from the project
        purger = create_scaling_group_for_project_purger(
            scaling_group=sgroup_name,
            project=project_id,
        )
        await scaling_group_repository.disassociate_scaling_group_with_user_groups(purger)

        # Then: Association should no longer exist
        association_exists = (
            await scaling_group_repository.check_scaling_group_user_group_association_exists(
                scaling_group=sgroup_name,
                user_group=project_id,
            )
        )
        assert association_exists is False

    async def test_disassociate_nonexistent_scaling_group_with_user_groups(
        self,
        scaling_group_repository: ScalingGroupRepository,
        sample_scaling_group_for_purge: str,
        test_user_domain_group: tuple[uuid.UUID, str, uuid.UUID],
    ) -> None:
        """Test disassociating a non-existent association does not raise error."""
        # Given: A scaling group that is NOT associated with a project
        sgroup_name = sample_scaling_group_for_purge
        _, _, project_id = test_user_domain_group

        # When: Disassociate (even though no association exists)
        purger = create_scaling_group_for_project_purger(
            scaling_group=sgroup_name,
            project=project_id,
        )
        # Then: Should not raise any error (BatchPurger deletes 0 rows silently)
        await scaling_group_repository.disassociate_scaling_group_with_user_groups(purger)

    @pytest.fixture
    async def sample_scaling_group_for_hierarchy(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[str, None]:
        sgroup_name = f"test-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as db_sess:
            sgroup = ScalingGroupRow(
                name=sgroup_name,
                description="Test scaling group for full hierarchy cascade delete",
                is_active=True,
                is_public=True,
                created_at=datetime.now(tz=UTC),
                wsproxy_addr=None,
                wsproxy_api_token=None,
                driver="static",
                driver_opts={},
                scheduler="fifo",
                scheduler_opts=ScalingGroupOpts(),
                use_host_network=False,
            )
            db_sess.add(sgroup)
            await db_sess.flush()
        yield sgroup_name

    @pytest.fixture
    async def sample_session(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_scaling_group_for_hierarchy: str,
        test_user_domain_group: tuple[uuid.UUID, str, uuid.UUID],
    ) -> AsyncGenerator[SessionId, None]:
        """Create a session referencing the scaling group."""
        test_user_uuid, test_domain, test_group_id = test_user_domain_group
        session_id = SessionId(uuid.uuid4())
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                SessionRow(
                    id=session_id,
                    domain_name=test_domain,
                    group_id=test_group_id,
                    user_uuid=test_user_uuid,
                    scaling_group_name=sample_scaling_group_for_hierarchy,
                    cluster_size=1,
                    vfolder_mounts={},
                )
            )
            await db_sess.flush()
        yield session_id

    @pytest.fixture
    async def sample_kernel(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_session: SessionId,
        test_user_domain_group: tuple[uuid.UUID, str, uuid.UUID],
    ) -> AsyncGenerator[None, None]:
        """Create a kernel for the session."""
        test_user_uuid, test_domain, test_group_id = test_user_domain_group
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                KernelRow(
                    session_id=sample_session,
                    domain_name=test_domain,
                    group_id=test_group_id,
                    user_uuid=test_user_uuid,
                    cluster_role=DEFAULT_ROLE,
                    occupied_slots=ResourceSlot(),
                    repl_in_port=0,
                    repl_out_port=0,
                    stdin_port=0,
                    stdout_port=0,
                    vfolder_mounts=None,
                )
            )
            await db_sess.flush()
        yield

    @pytest.fixture
    async def sample_endpoint(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_scaling_group_for_hierarchy: str,
        test_user_domain_group: tuple[uuid.UUID, str, uuid.UUID],
    ) -> AsyncGenerator[uuid.UUID, None]:
        """Create an endpoint referencing the scaling group."""
        test_user_uuid, test_domain, test_group_id = test_user_domain_group
        endpoint_id = uuid.uuid4()
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                EndpointRow(
                    id=endpoint_id,
                    name="test-endpoint-hierarchy",
                    domain=test_domain,
                    project=test_group_id,
                    resource_group=sample_scaling_group_for_hierarchy,
                    image=None,
                    lifecycle_stage=EndpointLifecycle.DESTROYED,
                    session_owner=test_user_uuid,
                    created_user=test_user_uuid,
                )
            )
            await db_sess.flush()
        yield endpoint_id

    @pytest.fixture
    async def sample_route(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_session: SessionId,
        sample_endpoint: uuid.UUID,
        test_user_domain_group: tuple[uuid.UUID, str, uuid.UUID],
    ) -> AsyncGenerator[None, None]:
        """Create a route connecting the session to the endpoint."""
        test_user_uuid, test_domain, test_group_id = test_user_domain_group
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                RoutingRow(
                    id=uuid.uuid4(),
                    endpoint=sample_endpoint,
                    session=sample_session,
                    session_owner=test_user_uuid,
                    domain=test_domain,
                    project=test_group_id,
                    traffic_ratio=1.0,
                )
            )
            await db_sess.flush()
        yield

    @pytest.mark.usefixtures("sample_kernel", "sample_route")
    async def test_purge_scaling_group_with_full_hierarchy(
        self,
        scaling_group_repository: ScalingGroupRepository,
        sample_scaling_group_for_hierarchy: str,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> None:
        """Test purging a scaling group with the full FK hierarchy.

        Hierarchy: ScalingGroup → Session → Kernel + Endpoint → Route
        """
        sgroup_name = sample_scaling_group_for_hierarchy

        purger = Purger(row_class=ScalingGroupRow, pk_value=sgroup_name)
        result = await scaling_group_repository.purge_scaling_group(purger)

        assert result.name == sgroup_name

        async with db_with_cleanup.begin_readonly_session() as db_sess:
            sg_result = await db_sess.execute(
                sa.select(ScalingGroupRow).where(ScalingGroupRow.name == sgroup_name)
            )
            assert sg_result.scalar_one_or_none() is None
