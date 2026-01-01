import uuid
from collections.abc import AsyncGenerator, Callable
from datetime import datetime
from typing import Any, Optional

import pytest
import sqlalchemy as sa

from ai.backend.common.exception import ScalingGroupConflict
from ai.backend.common.types import SessionTypes
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.user.types import UserStatus
from ai.backend.manager.errors.resource import ScalingGroupNotFound
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.endpoint import EndpointLifecycle, EndpointRow
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.models.scaling_group import ScalingGroupOpts, ScalingGroupRow
from ai.backend.manager.models.session import SessionId, SessionRow
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import VFolderRow
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.base.purger import Purger
from ai.backend.manager.repositories.scaling_group import ScalingGroupRepository
from ai.backend.manager.repositories.scaling_group.creators import ScalingGroupCreatorSpec
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
                # FK dependency order: parents first
                DomainRow,
                ProjectResourcePolicyRow,
                UserResourcePolicyRow,
                KeyPairResourcePolicyRow,
                ScalingGroupRow,
                UserRow,
                KeyPairRow,
                GroupRow,
                SessionRow,
                VFolderRow,
                EndpointRow,
                RoutingRow,
            ],
        ):
            yield database_connection

    def _create_scaling_group_creator(
        self,
        name: str,
        driver: str = "static",
        scheduler: str = "fifo",
        description: Optional[str] = None,
        is_active: bool = True,
        is_public: bool = True,
        wsproxy_addr: Optional[str] = None,
        wsproxy_api_token: Optional[str] = None,
        driver_opts: Optional[dict[str, Any]] = None,
        scheduler_opts: Optional[ScalingGroupOpts] = None,
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
                    created_at=datetime.now(),
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
                created_at=datetime.now(),
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
                total_resource_slots={},
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
                created_at=datetime.now(),
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
                created_at=datetime.now(),
                domain_name=test_domain,
                total_resource_slots={},
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
                created_at=datetime.now(),
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
        repo = ScalingGroupRepository(db=db_with_cleanup)
        yield repo

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
