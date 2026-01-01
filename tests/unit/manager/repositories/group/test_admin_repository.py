"""Tests for AdminGroupRepository._delete_group_endpoints functionality"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest
import sqlalchemy as sa

from ai.backend.common.types import ResourceSlot
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.group.types import ProjectType
from ai.backend.manager.data.model_serving.types import EndpointLifecycle
from ai.backend.manager.errors.resource import ProjectHasActiveEndpointsError
from ai.backend.manager.models import (
    DomainRow,
    EndpointRow,
    GroupRow,
    ProjectResourcePolicyRow,
    RoutingRow,
    ScalingGroupRow,
    SessionRow,
    UserResourcePolicyRow,
    UserRow,
)
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.resource_policy import KeyPairResourcePolicyRow
from ai.backend.manager.models.scaling_group import ScalingGroupOpts
from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.models.user import UserRole, UserStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import VFolderRow
from ai.backend.manager.repositories.group.admin_repository import AdminGroupRepository
from ai.backend.testutils.db import with_tables


class TestAdminGroupRepositoryDeleteEndpoints:
    """Test cases for AdminGroupRepository._delete_group_endpoints"""

    @pytest.fixture
    def test_password_info(self) -> PasswordInfo:
        """Create a test PasswordInfo object"""
        return PasswordInfo(
            password="test_password",
            algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
            rounds=100_000,
            salt_size=32,
        )

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
                UserResourcePolicyRow,
                KeyPairResourcePolicyRow,
                ProjectResourcePolicyRow,
                UserRow,
                KeyPairRow,
                GroupRow,
                ScalingGroupRow,
                AgentRow,
                SessionRow,
                KernelRow,
                VFolderRow,
                EndpointRow,
                RoutingRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def test_domain(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
        """Create test domain"""
        domain_name = f"test-domain-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as session:
            domain = DomainRow(
                name=domain_name,
                description="Test domain",
                is_active=True,
                total_resource_slots=ResourceSlot.from_user_input({"cpu": "4", "mem": "8g"}, None),
                allowed_vfolder_hosts={},
                allowed_docker_registries=[],
                dotfiles=b"",
                integration_id=None,
            )
            session.add(domain)
            await session.commit()

        return domain_name

    @pytest.fixture
    async def test_user(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain: str,
        test_password_info: PasswordInfo,
    ) -> uuid.UUID:
        """Create test user"""
        user_uuid = uuid.uuid4()
        policy_name = f"test-policy-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as session:
            # Create user resource policy
            policy = UserResourcePolicyRow(
                name=policy_name,
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_session_count_per_model_session=10,
                max_customized_image_count=10,
            )
            session.add(policy)

            # Create user
            user = UserRow(
                uuid=user_uuid,
                username=f"testuser-{user_uuid.hex[:8]}",
                email=f"test-{user_uuid.hex[:8]}@example.com",
                password=test_password_info,
                need_password_change=False,
                full_name="Test User",
                description="Test user",
                status=UserStatus.ACTIVE,
                status_info="active",
                domain_name=test_domain,
                role=UserRole.USER,
                resource_policy=policy_name,
            )
            session.add(user)
            await session.commit()

        return user_uuid

    @pytest.fixture
    async def test_group(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain: str,
    ) -> uuid.UUID:
        """Create test group"""
        group_id = uuid.uuid4()
        policy_name = f"test-policy-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as session:
            # Create project resource policy
            policy = ProjectResourcePolicyRow(
                name=policy_name,
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_network_count=3,
            )
            session.add(policy)

            # Create group
            group = GroupRow(
                id=group_id,
                name=f"test-group-{group_id.hex[:8]}",
                description="Test group",
                is_active=True,
                domain_name=test_domain,
                total_resource_slots={},
                allowed_vfolder_hosts={},
                integration_id=None,
                resource_policy=policy_name,
                type=ProjectType.GENERAL,
            )
            session.add(group)
            await session.commit()

        return group_id

    @pytest.fixture
    async def storage_manager_mock(self) -> StorageSessionManager:
        """Create a mock StorageSessionManager"""
        from unittest.mock import Mock

        return Mock(spec=StorageSessionManager)

    @pytest.fixture
    async def admin_group_repository(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        storage_manager_mock: StorageSessionManager,
    ) -> AdminGroupRepository:
        """Create AdminGroupRepository instance"""
        return AdminGroupRepository(
            db=db_with_cleanup,
            storage_manager=storage_manager_mock,
        )

    # Test-specific fixtures

    @pytest.fixture
    async def inactive_endpoints_with_routings(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain: str,
        test_user: uuid.UUID,
        test_group: uuid.UUID,
    ) -> list[uuid.UUID]:
        """Create two inactive endpoints with routing entries (no sessions)"""
        endpoint_ids = []
        sgroup_name = f"default-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as session:
            # Create scaling group
            sgroup = ScalingGroupRow(
                name=sgroup_name,
                description="Test scaling group",
                is_active=True,
                driver="static",
                driver_opts={},
                scheduler="fifo",
                scheduler_opts=ScalingGroupOpts(),
            )
            session.add(sgroup)
            await session.flush()
            # Create two inactive endpoints (use DESTROYED to avoid image requirement)
            for i in range(2):
                endpoint_id = uuid.uuid4()
                endpoint = EndpointRow(
                    id=endpoint_id,
                    name=f"test-endpoint-{i}-{uuid.uuid4().hex[:8]}",
                    created_user=test_user,
                    session_owner=test_user,
                    replicas=1,
                    desired_replicas=1,
                    image=None,
                    domain=test_domain,
                    project=test_group,
                    resource_group=sgroup_name,
                    lifecycle_stage=EndpointLifecycle.DESTROYED,  # Use DESTROYED to avoid image requirement
                    resource_slots={},
                    cluster_mode="single-node",
                    cluster_size=1,
                )
                session.add(endpoint)
                endpoint_ids.append(endpoint_id)

                # Create routing entry without session
                routing = RoutingRow(
                    id=uuid.uuid4(),
                    endpoint=endpoint_id,
                    session=None,
                    session_owner=test_user,
                    domain=test_domain,
                    project=test_group,
                    traffic_ratio=1.0,
                )
                session.add(routing)

            await session.commit()

        return endpoint_ids

    @pytest.fixture
    async def inactive_endpoint_with_session_and_routing(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain: str,
        test_user: uuid.UUID,
        test_group: uuid.UUID,
    ) -> dict[str, uuid.UUID]:
        """Create one inactive endpoint with a session and routing entry"""
        endpoint_id = uuid.uuid4()
        session_id = uuid.uuid4()
        sgroup_name = f"default-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as session:
            # Create scaling group
            sgroup = ScalingGroupRow(
                name=sgroup_name,
                description="Test scaling group",
                is_active=True,
                driver="static",
                driver_opts={},
                scheduler="fifo",
                scheduler_opts=ScalingGroupOpts(),
            )
            session.add(sgroup)
            await session.flush()

            # Create endpoint (use DESTROYED to avoid image requirement)
            endpoint = EndpointRow(
                id=endpoint_id,
                name=f"test-endpoint-{uuid.uuid4().hex[:8]}",
                created_user=test_user,
                session_owner=test_user,
                replicas=1,
                desired_replicas=1,
                image=None,
                domain=test_domain,
                project=test_group,
                resource_group=sgroup_name,
                lifecycle_stage=EndpointLifecycle.DESTROYED,
                resource_slots={},
                cluster_mode="single-node",
                cluster_size=1,
            )
            session.add(endpoint)

            # Create session
            session_row = SessionRow(
                id=session_id,
                creation_id=f"test-session-{uuid.uuid4().hex[:8]}",
                domain_name=test_domain,
                group_id=test_group,
                user_uuid=test_user,
                access_key="test-access-key",
                cluster_mode="single-node",
                cluster_size=1,
                images=[],
                vfolder_mounts=[],
                agent_ids=[],
                designated_agent_ids=[],
                target_sgroup_names=[],
            )
            session.add(session_row)

            # Create routing with session
            routing = RoutingRow(
                id=uuid.uuid4(),
                endpoint=endpoint_id,
                session=session_id,
                session_owner=test_user,
                domain=test_domain,
                project=test_group,
                traffic_ratio=1.0,
            )
            session.add(routing)

            await session.commit()

        return {"endpoint_id": endpoint_id, "session_id": session_id}

    @pytest.fixture
    async def active_endpoint(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain: str,
        test_user: uuid.UUID,
        test_group: uuid.UUID,
    ) -> uuid.UUID:
        """Create one active endpoint (lifecycle_stage=CREATED)"""
        endpoint_id = uuid.uuid4()
        image_id = uuid.uuid4()
        sgroup_name = f"default-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as session:
            # Create scaling group
            sgroup = ScalingGroupRow(
                name=sgroup_name,
                description="Test scaling group",
                is_active=True,
                driver="static",
                driver_opts={},
                scheduler="fifo",
                scheduler_opts=ScalingGroupOpts(),
            )
            session.add(sgroup)
            await session.flush()

            endpoint = EndpointRow(
                id=endpoint_id,
                name=f"test-endpoint-{uuid.uuid4().hex[:8]}",
                created_user=test_user,
                session_owner=test_user,
                replicas=1,
                desired_replicas=1,
                image=image_id,  # Active endpoints require image
                domain=test_domain,
                project=test_group,
                resource_group=sgroup_name,
                lifecycle_stage=EndpointLifecycle.CREATED,  # Active!
                resource_slots={},
                cluster_mode="single-node",
                cluster_size=1,
            )
            session.add(endpoint)
            await session.commit()

        return endpoint_id

    @pytest.fixture
    async def multiple_endpoints_with_sessions(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain: str,
        test_user: uuid.UUID,
        test_group: uuid.UUID,
    ) -> dict[str, list[uuid.UUID]]:
        """Create 3 inactive endpoints, each with a session and routing entry"""
        endpoint_ids = []
        session_ids = []
        sgroup_name = f"default-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as session:
            # Create scaling group
            sgroup = ScalingGroupRow(
                name=sgroup_name,
                description="Test scaling group",
                is_active=True,
                driver="static",
                driver_opts={},
                scheduler="fifo",
                scheduler_opts=ScalingGroupOpts(),
            )
            session.add(sgroup)
            await session.flush()
            for i in range(3):
                endpoint_id = uuid.uuid4()
                session_id = uuid.uuid4()

                # Create endpoint (use DESTROYED to avoid image requirement)
                endpoint = EndpointRow(
                    id=endpoint_id,
                    name=f"test-endpoint-{i}-{uuid.uuid4().hex[:8]}",
                    created_user=test_user,
                    session_owner=test_user,
                    replicas=1,
                    desired_replicas=1,
                    image=None,
                    domain=test_domain,
                    project=test_group,
                    resource_group=sgroup_name,
                    lifecycle_stage=EndpointLifecycle.DESTROYED,
                    resource_slots={},
                    cluster_mode="single-node",
                    cluster_size=1,
                )
                session.add(endpoint)
                endpoint_ids.append(endpoint_id)

                # Create session
                session_row = SessionRow(
                    id=session_id,
                    creation_id=f"test-session-{i}-{uuid.uuid4().hex[:8]}",
                    domain_name=test_domain,
                    group_id=test_group,
                    user_uuid=test_user,
                    access_key=f"test-access-key-{i}",
                    cluster_mode="single-node",
                    cluster_size=1,
                    images=[],
                    vfolder_mounts=[],
                    agent_ids=[],
                    designated_agent_ids=[],
                    target_sgroup_names=[],
                )
                session.add(session_row)
                session_ids.append(session_id)

                # Create routing
                routing = RoutingRow(
                    id=uuid.uuid4(),
                    endpoint=endpoint_id,
                    session=session_id,
                    session_owner=test_user,
                    domain=test_domain,
                    project=test_group,
                    traffic_ratio=1.0,
                )
                session.add(routing)

            await session.commit()

        return {"endpoint_ids": endpoint_ids, "session_ids": session_ids}

    # Test cases

    @pytest.mark.asyncio
    async def test_delete_group_endpoints_success(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        admin_group_repository: AdminGroupRepository,
        test_group: uuid.UUID,
        inactive_endpoints_with_routings: list[uuid.UUID],
    ) -> None:
        """Test successful deletion of endpoints with routing entries"""
        # Call _delete_group_endpoints
        async with db_with_cleanup.begin_session() as session:
            await admin_group_repository._delete_group_endpoints(session, test_group)
            await session.commit()

        # Verify all data is deleted
        async with db_with_cleanup.begin_session() as session:
            # Check endpoints are deleted
            endpoints_result = await session.execute(
                sa.select(EndpointRow).where(EndpointRow.project == test_group)
            )
            assert len(endpoints_result.all()) == 0

            # Check routings are deleted
            routings_result = await session.execute(
                sa.select(RoutingRow).where(RoutingRow.project == test_group)
            )
            assert len(routings_result.all()) == 0

    @pytest.mark.asyncio
    async def test_delete_group_endpoints_with_sessions(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        admin_group_repository: AdminGroupRepository,
        test_group: uuid.UUID,
        inactive_endpoint_with_session_and_routing: dict[str, uuid.UUID],
    ) -> None:
        """Test deletion of endpoints with associated sessions"""
        endpoint_id = inactive_endpoint_with_session_and_routing["endpoint_id"]
        session_id = inactive_endpoint_with_session_and_routing["session_id"]

        # Call _delete_group_endpoints
        async with db_with_cleanup.begin_session() as session:
            await admin_group_repository._delete_group_endpoints(session, test_group)
            await session.commit()

        # Verify all data is deleted
        async with db_with_cleanup.begin_session() as session:
            # Check session is deleted
            sessions_result = await session.execute(
                sa.select(SessionRow).where(SessionRow.id == session_id)
            )
            assert len(sessions_result.all()) == 0

            # Check routing is deleted
            routings_result = await session.execute(
                sa.select(RoutingRow).where(RoutingRow.endpoint == endpoint_id)
            )
            assert len(routings_result.all()) == 0

            # Check endpoint is deleted
            endpoints_result = await session.execute(
                sa.select(EndpointRow).where(EndpointRow.id == endpoint_id)
            )
            assert len(endpoints_result.all()) == 0

    @pytest.mark.asyncio
    async def test_delete_group_endpoints_with_active_endpoints(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        admin_group_repository: AdminGroupRepository,
        test_group: uuid.UUID,
        active_endpoint: uuid.UUID,
    ) -> None:
        """Test that active endpoints raise an exception"""
        # Call _delete_group_endpoints and expect exception
        with pytest.raises(ProjectHasActiveEndpointsError):
            async with db_with_cleanup.begin_session() as session:
                await admin_group_repository._delete_group_endpoints(session, test_group)

        # Verify endpoint is NOT deleted
        async with db_with_cleanup.begin_session() as session:
            endpoints_result = await session.execute(
                sa.select(EndpointRow).where(EndpointRow.id == active_endpoint)
            )
            assert len(endpoints_result.all()) == 1

    @pytest.mark.asyncio
    async def test_delete_group_endpoints_empty(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        admin_group_repository: AdminGroupRepository,
        test_group: uuid.UUID,
    ) -> None:
        """Test deletion with no endpoints (should complete without errors)"""
        # Call _delete_group_endpoints on group with no endpoints
        async with db_with_cleanup.begin_session() as session:
            # Should not raise any exception
            await admin_group_repository._delete_group_endpoints(session, test_group)
            await session.commit()

        # Verify no errors occurred (test passes if no exception raised)

    @pytest.mark.asyncio
    async def test_delete_group_endpoints_no_synchronize_session_error(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        admin_group_repository: AdminGroupRepository,
        test_group: uuid.UUID,
        multiple_endpoints_with_sessions: dict[str, list[uuid.UUID]],
    ) -> None:
        """
        Test that the fix prevents synchronize_session errors.

        This test verifies the bug fix where execution_options={"synchronize_session": False}
        was added to prevent SQLAlchemy errors during bulk delete operations.
        """
        endpoint_ids = multiple_endpoints_with_sessions["endpoint_ids"]
        session_ids = multiple_endpoints_with_sessions["session_ids"]

        # This should NOT raise synchronize_session errors thanks to the fix
        async with db_with_cleanup.begin_session() as session:
            await admin_group_repository._delete_group_endpoints(session, test_group)
            await session.commit()

        # Verify all data is deleted
        async with db_with_cleanup.begin_session() as session:
            sessions_result = await session.execute(
                sa.select(SessionRow).where(SessionRow.id.in_(session_ids))
            )
            assert len(sessions_result.all()) == 0

            routings_result = await session.execute(
                sa.select(RoutingRow).where(RoutingRow.endpoint.in_(endpoint_ids))
            )
            assert len(routings_result.all()) == 0

            endpoints_result = await session.execute(
                sa.select(EndpointRow).where(EndpointRow.id.in_(endpoint_ids))
            )
            assert len(endpoints_result.all()) == 0
