"""Tests for GroupRepository functionality"""

from __future__ import annotations

import json
import uuid
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import pytest
import sqlalchemy as sa

from ai.backend.common.exception import InvalidAPIParameters
from ai.backend.common.types import (
    QuotaScopeID,
    QuotaScopeType,
    ResourceSlot,
    VFolderHostPermission,
    VFolderHostPermissionMap,
    VFolderUsageMode,
)
from ai.backend.manager.data.agent.types import AgentStatus
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.group.types import ProjectType
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.model_serving.types import EndpointLifecycle
from ai.backend.manager.data.vfolder.types import VFolderMountPermission as VFolderPermission
from ai.backend.manager.data.vfolder.types import (
    VFolderOperationStatus,
    VFolderOwnershipType,
)
from ai.backend.manager.errors.resource import (
    ProjectHasActiveEndpointsError,
    ProjectHasActiveKernelsError,
    ProjectHasVFoldersMountedError,
    ProjectNotFound,
)
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.deployment_auto_scaling_policy import DeploymentAutoScalingPolicyRow
from ai.backend.manager.models.deployment_policy import DeploymentPolicyRow
from ai.backend.manager.models.deployment_revision import DeploymentRevisionRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.models.group import AssocGroupUserRow, GroupRow, association_groups_users
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
from ai.backend.manager.models.scaling_group import ScalingGroupOpts, ScalingGroupRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.models.user import UserRole, UserRow, UserStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import VFolderRow
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.group.creators import GroupCreatorSpec
from ai.backend.manager.repositories.group.repository import GroupRepository
from ai.backend.manager.repositories.group.updaters import GroupUpdaterSpec
from ai.backend.manager.types import OptionalState, TriState
from ai.backend.testutils.db import with_tables


class TestGroupRepositoryDeleteEndpoints:
    """Test cases for GroupRepository._delete_group_endpoints"""

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
                ScalingGroupRow,
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                KeyPairResourcePolicyRow,
                UserRoleRow,
                UserRow,
                KeyPairRow,
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
        return MagicMock(spec=StorageSessionManager)

    @pytest.fixture
    async def group_repository(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        storage_manager_mock: StorageSessionManager,
    ) -> GroupRepository:
        """Create GroupRepository instance"""
        return GroupRepository(
            db=db_with_cleanup,
            config_provider=MagicMock(),
            valkey_stat_client=MagicMock(),
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

    async def test_delete_group_endpoints_success(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        group_repository: GroupRepository,
        test_group: uuid.UUID,
        inactive_endpoints_with_routings: list[uuid.UUID],
    ) -> None:
        """Test successful deletion of endpoints with routing entries"""
        # Call _delete_group_endpoints
        async with db_with_cleanup.begin_session() as session:
            await group_repository._delete_group_endpoints(session, test_group)
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

    async def test_delete_group_endpoints_with_sessions(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        group_repository: GroupRepository,
        test_group: uuid.UUID,
        inactive_endpoint_with_session_and_routing: dict[str, uuid.UUID],
    ) -> None:
        """Test deletion of endpoints with associated sessions"""
        endpoint_id = inactive_endpoint_with_session_and_routing["endpoint_id"]
        session_id = inactive_endpoint_with_session_and_routing["session_id"]

        # Call _delete_group_endpoints
        async with db_with_cleanup.begin_session() as session:
            await group_repository._delete_group_endpoints(session, test_group)
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

    async def test_delete_group_endpoints_with_active_endpoints(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        group_repository: GroupRepository,
        test_group: uuid.UUID,
        active_endpoint: uuid.UUID,
    ) -> None:
        """Test that active endpoints raise an exception"""
        # Call _delete_group_endpoints and expect exception
        with pytest.raises(ProjectHasActiveEndpointsError):
            async with db_with_cleanup.begin_session() as session:
                await group_repository._delete_group_endpoints(session, test_group)

        # Verify endpoint is NOT deleted
        async with db_with_cleanup.begin_session() as session:
            endpoints_result = await session.execute(
                sa.select(EndpointRow).where(EndpointRow.id == active_endpoint)
            )
            assert len(endpoints_result.all()) == 1

    async def test_delete_group_endpoints_empty(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        group_repository: GroupRepository,
        test_group: uuid.UUID,
    ) -> None:
        """Test deletion with no endpoints (should complete without errors)"""
        # Call _delete_group_endpoints on group with no endpoints
        async with db_with_cleanup.begin_session() as session:
            # Should not raise any exception
            await group_repository._delete_group_endpoints(session, test_group)
            await session.commit()

        # Verify no errors occurred (test passes if no exception raised)

    async def test_delete_group_endpoints_no_synchronize_session_error(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        group_repository: GroupRepository,
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
            await group_repository._delete_group_endpoints(session, test_group)
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


class TestGroupRepositoryCreateResourcePolicyValidation:
    """Tests for resource_policy validation in GroupRepository.create()"""

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        """Database connection with tables created."""
        async with with_tables(
            database_connection,
            [
                DomainRow,
                ProjectResourcePolicyRow,
                GroupRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def test_domain(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
        """Create test domain."""
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
    async def project_resource_policy(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
        """Create a project resource policy."""
        policy_name = f"test-project-policy-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as session:
            policy = ProjectResourcePolicyRow(
                name=policy_name,
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_network_count=3,
            )
            session.add(policy)
            await session.commit()

        return policy_name

    @pytest.fixture
    async def group_repository_with_mock_role_manager(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> GroupRepository:
        """GroupRepository with mocked RoleManager for create tests."""
        repo = GroupRepository(
            db=db_with_cleanup,
            config_provider=MagicMock(),
            valkey_stat_client=MagicMock(),
            storage_manager=MagicMock(spec=StorageSessionManager),
        )
        mock_role_manager = MagicMock()
        mock_role_manager.create_system_role = AsyncMock(return_value=None)
        repo._role_manager = mock_role_manager
        return repo

    @pytest.mark.asyncio
    async def test_create_succeeds_with_existing_project_resource_policy(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        group_repository_with_mock_role_manager: GroupRepository,
        test_domain: str,
        project_resource_policy: str,
    ) -> None:
        """Test that group creation succeeds when project_resource_policy exists."""
        spec = GroupCreatorSpec(
            name=f"test-group-{uuid.uuid4().hex[:8]}",
            domain_name=test_domain,
            description="Test group",
            is_active=True,
            total_resource_slots=ResourceSlot({}),
            allowed_vfolder_hosts=VFolderHostPermissionMap(),
            integration_id=None,
            resource_policy=project_resource_policy,
            type=ProjectType.GENERAL,
        )
        creator = Creator(spec=spec)

        result = await group_repository_with_mock_role_manager.create(creator)

        assert result.name == spec.name
        assert result.resource_policy == project_resource_policy

    @pytest.mark.asyncio
    async def test_create_fails_with_nonexistent_project_resource_policy(
        self,
        group_repository_with_mock_role_manager: GroupRepository,
        test_domain: str,
    ) -> None:
        """Test that group creation fails when project_resource_policy does not exist."""
        nonexistent_policy = "nonexistent-policy"
        spec = GroupCreatorSpec(
            name=f"test-group-{uuid.uuid4().hex[:8]}",
            domain_name=test_domain,
            description="Test group",
            is_active=True,
            total_resource_slots=ResourceSlot({}),
            allowed_vfolder_hosts=VFolderHostPermissionMap(),
            integration_id=None,
            resource_policy=nonexistent_policy,
            type=ProjectType.GENERAL,
        )
        creator = Creator(spec=spec)

        with pytest.raises(InvalidAPIParameters) as exc_info:
            await group_repository_with_mock_role_manager.create(creator)

        assert "Resource policy" in str(exc_info.value)
        assert "does not exist" in str(exc_info.value)


class TestGroupRepository:
    """Test cases for GroupRepository CRUD operations"""

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
                ScalingGroupRow,
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                KeyPairResourcePolicyRow,
                UserRoleRow,
                UserRow,
                KeyPairRow,
                GroupRow,
                AssocGroupUserRow,  # User-Group association table
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
    async def default_project_resource_policy(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
        """Create default project resource policy"""
        policy_name = "default"

        async with db_with_cleanup.begin_session() as session:
            policy = ProjectResourcePolicyRow(
                name=policy_name,
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_network_count=3,
            )
            session.add(policy)
            await session.commit()

        return policy_name

    @pytest.fixture
    async def default_user_resource_policy(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
        """Create default user resource policy"""
        policy_name = "default"

        async with db_with_cleanup.begin_session() as session:
            policy = UserResourcePolicyRow(
                name=policy_name,
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_session_count_per_model_session=10,
                max_customized_image_count=10,
            )
            session.add(policy)
            await session.commit()

        return policy_name

    @pytest.fixture
    async def test_user(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain: str,
        default_user_resource_policy: str,
        test_password_info: PasswordInfo,
    ) -> uuid.UUID:
        """Create test user"""
        user_uuid = uuid.uuid4()

        async with db_with_cleanup.begin_session() as session:
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
                resource_policy=default_user_resource_policy,
            )
            session.add(user)
            await session.commit()

        return user_uuid

    @pytest.fixture
    async def test_users_for_group(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain: str,
        default_user_resource_policy: str,
        test_password_info: PasswordInfo,
    ) -> list[uuid.UUID]:
        """Create multiple test users for group user management tests"""
        user_uuids = []

        async with db_with_cleanup.begin_session() as session:
            for i in range(3):
                user_uuid = uuid.uuid4()
                user = UserRow(
                    uuid=user_uuid,
                    username=f"testuser-{i}-{user_uuid.hex[:8]}",
                    email=f"test-{i}-{user_uuid.hex[:8]}@example.com",
                    password=test_password_info,
                    need_password_change=False,
                    full_name=f"Test User {i}",
                    description="Test user",
                    status=UserStatus.ACTIVE,
                    status_info="active",
                    domain_name=test_domain,
                    role=UserRole.USER,
                    resource_policy=default_user_resource_policy,
                )
                session.add(user)
                user_uuids.append(user_uuid)
            await session.commit()

        return user_uuids

    @pytest.fixture
    async def test_group(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain: str,
        default_project_resource_policy: str,
    ) -> uuid.UUID:
        """Create test group"""
        group_id = uuid.uuid4()

        async with db_with_cleanup.begin_session() as session:
            group = GroupRow(
                id=group_id,
                name=f"test-group-{group_id.hex[:8]}",
                description="Test group",
                is_active=True,
                domain_name=test_domain,
                total_resource_slots={},
                allowed_vfolder_hosts={},
                integration_id="test-integration-id",
                resource_policy=default_project_resource_policy,
                type=ProjectType.GENERAL,
            )
            session.add(group)
            await session.commit()

        return group_id

    @pytest.fixture
    async def storage_manager_mock(self) -> StorageSessionManager:
        """Create a mock StorageSessionManager"""
        return MagicMock(spec=StorageSessionManager)

    @pytest.fixture
    async def group_repository(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        storage_manager_mock: StorageSessionManager,
    ) -> GroupRepository:
        """Create GroupRepository instance"""
        return GroupRepository(
            db=db_with_cleanup,
            config_provider=MagicMock(),
            valkey_stat_client=MagicMock(),
            storage_manager=storage_manager_mock,
        )

    @pytest.fixture
    async def group_repository_with_mock_role_manager(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        storage_manager_mock: StorageSessionManager,
    ) -> GroupRepository:
        """GroupRepository with mocked RoleManager for create tests"""
        repo = GroupRepository(
            db=db_with_cleanup,
            config_provider=MagicMock(),
            valkey_stat_client=MagicMock(),
            storage_manager=storage_manager_mock,
        )
        mock_role_manager = MagicMock()
        mock_role_manager.create_system_role = AsyncMock(return_value=None)
        repo._role_manager = mock_role_manager
        return repo

    @pytest.fixture
    async def test_scaling_group(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
        """Create test scaling group"""
        sgroup_name = f"test-sgroup-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as session:
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
            await session.commit()

        return sgroup_name

    @pytest.fixture
    async def group_with_active_kernel(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain: str,
        test_user: uuid.UUID,
        default_project_resource_policy: str,
        test_scaling_group: str,
    ) -> uuid.UUID:
        """Create a group with an active kernel"""
        group_id = uuid.uuid4()
        session_id = uuid.uuid4()
        kernel_id = uuid.uuid4()
        agent_id = f"test-agent-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as session:
            # Create group
            group = GroupRow(
                id=group_id,
                name=f"group-with-kernel-{group_id.hex[:8]}",
                description="Group with active kernel",
                is_active=True,
                domain_name=test_domain,
                total_resource_slots={},
                allowed_vfolder_hosts={},
                integration_id=None,
                resource_policy=default_project_resource_policy,
                type=ProjectType.GENERAL,
            )
            session.add(group)

            # Create agent
            agent = AgentRow(
                id=agent_id,
                status=AgentStatus.ALIVE,
                region="local",
                scaling_group=test_scaling_group,
                schedulable=True,
                available_slots=ResourceSlot({}),
                occupied_slots=ResourceSlot({}),
                addr="tcp://127.0.0.1:5001",
                version="1.0.0",
                architecture="x86_64",
            )
            session.add(agent)

            # Create session
            session_row = SessionRow(
                id=session_id,
                creation_id=f"test-session-{uuid.uuid4().hex[:8]}",
                domain_name=test_domain,
                group_id=group_id,
                user_uuid=test_user,
                access_key="test-access-key",
                cluster_mode="single-node",
                cluster_size=1,
                images=[],
                vfolder_mounts=[],
                agent_ids=[agent_id],
                designated_agent_ids=[],
                target_sgroup_names=[test_scaling_group],
            )
            session.add(session_row)

            # Create kernel with active status (RUNNING is in AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES)
            kernel = KernelRow(
                id=kernel_id,
                session_id=session_id,
                domain_name=test_domain,
                group_id=group_id,
                user_uuid=test_user,
                access_key="test-access-key",
                agent=agent_id,
                agent_addr="tcp://127.0.0.1:5001",
                cluster_role="main",
                cluster_idx=0,
                cluster_hostname=f"kernel-{kernel_id.hex[:8]}",
                status=KernelStatus.RUNNING,
                occupied_slots=ResourceSlot({}),
                repl_in_port=0,
                repl_out_port=0,
                stdin_port=0,
                stdout_port=0,
                vfolder_mounts={},
                mounts=[],
            )
            session.add(kernel)
            await session.commit()

        return group_id

    @pytest.fixture
    async def group_with_active_endpoint(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain: str,
        test_user: uuid.UUID,
        default_project_resource_policy: str,
        test_scaling_group: str,
    ) -> uuid.UUID:
        """Create a group with an active endpoint"""
        group_id = uuid.uuid4()
        endpoint_id = uuid.uuid4()

        async with db_with_cleanup.begin_session() as session:
            # Create group first
            group = GroupRow(
                id=group_id,
                name=f"group-with-endpoint-{group_id.hex[:8]}",
                description="Group with active endpoint",
                is_active=True,
                domain_name=test_domain,
                total_resource_slots={},
                allowed_vfolder_hosts={},
                integration_id=None,
                resource_policy=default_project_resource_policy,
                type=ProjectType.GENERAL,
            )
            session.add(group)
            await session.flush()  # Flush to satisfy FK constraint

            # Create active endpoint (CREATED lifecycle stage)
            endpoint = EndpointRow(
                id=endpoint_id,
                name=f"active-endpoint-{uuid.uuid4().hex[:8]}",
                created_user=test_user,
                session_owner=test_user,
                replicas=1,
                desired_replicas=1,
                image=uuid.uuid4(),  # Active endpoints need image
                domain=test_domain,
                project=group_id,
                resource_group=test_scaling_group,
                lifecycle_stage=EndpointLifecycle.CREATED,
                resource_slots={},
                cluster_mode="single-node",
                cluster_size=1,
            )
            session.add(endpoint)
            await session.commit()

        return group_id

    @pytest.fixture
    async def group_with_mounted_vfolders(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain: str,
        test_user: uuid.UUID,
        default_project_resource_policy: str,
        test_scaling_group: str,
    ) -> uuid.UUID:
        """Create a group with vfolders mounted to active kernels"""
        group_id = uuid.uuid4()
        vfolder_id = uuid.uuid4()
        session_id = uuid.uuid4()
        kernel_id = uuid.uuid4()
        agent_id = f"test-agent-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as session:
            # Create group first
            group = GroupRow(
                id=group_id,
                name=f"group-with-vfolder-{group_id.hex[:8]}",
                description="Group with mounted vfolders",
                is_active=True,
                domain_name=test_domain,
                total_resource_slots={},
                allowed_vfolder_hosts={},
                integration_id=None,
                resource_policy=default_project_resource_policy,
                type=ProjectType.GENERAL,
            )
            session.add(group)
            await session.flush()  # Flush to satisfy FK constraint

            # Create vfolder belonging to the group
            vfolder = VFolderRow(
                id=vfolder_id,
                name=f"test-vfolder-{vfolder_id.hex[:8]}",
                host="local",
                domain_name=test_domain,
                group=group_id,
                user=test_user,
                quota_scope_id=QuotaScopeID(QuotaScopeType.PROJECT, group_id),
                usage_mode=VFolderUsageMode.GENERAL,
                permission=VFolderPermission.READ_WRITE,
                ownership_type=VFolderOwnershipType.GROUP,
                status=VFolderOperationStatus.READY,
            )
            session.add(vfolder)

            # Create agent
            agent = AgentRow(
                id=agent_id,
                status=AgentStatus.ALIVE,
                region="local",
                scaling_group=test_scaling_group,
                schedulable=True,
                available_slots=ResourceSlot({}),
                occupied_slots=ResourceSlot({}),
                addr="tcp://127.0.0.1:5001",
                version="1.0.0",
                architecture="x86_64",
            )
            session.add(agent)

            # Create session
            session_row = SessionRow(
                id=session_id,
                creation_id=f"test-session-{uuid.uuid4().hex[:8]}",
                domain_name=test_domain,
                group_id=group_id,
                user_uuid=test_user,
                access_key="test-access-key",
                cluster_mode="single-node",
                cluster_size=1,
                images=[],
                vfolder_mounts=[],
                agent_ids=[agent_id],
                designated_agent_ids=[],
                target_sgroup_names=[test_scaling_group],
            )
            session.add(session_row)

            # Create kernel with vfolder mounted
            # mounts format: list of [name, host, vfolder_id_str, ...]
            kernel = KernelRow(
                id=kernel_id,
                session_id=session_id,
                domain_name=test_domain,
                group_id=group_id,
                user_uuid=test_user,
                access_key="test-access-key",
                agent=agent_id,
                agent_addr="tcp://127.0.0.1:5001",
                cluster_role="main",
                cluster_idx=0,
                cluster_hostname=f"kernel-{kernel_id.hex[:8]}",
                status=KernelStatus.RUNNING,
                occupied_slots=ResourceSlot({}),
                repl_in_port=0,
                repl_out_port=0,
                stdin_port=0,
                stdout_port=0,
                vfolder_mounts={},
                mounts=[["test-vfolder", "local", str(vfolder_id)]],
            )
            session.add(kernel)
            await session.commit()

        return group_id

    # ===========================================
    # Tests for create method
    # ===========================================

    async def test_create_success(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        group_repository_with_mock_role_manager: GroupRepository,
        test_domain: str,
        default_project_resource_policy: str,
    ) -> None:
        """Test successful group creation with valid domain and resource_policy."""
        creator_spec = GroupCreatorSpec(
            name="test-new-group",
            domain_name=test_domain,
            description="Test group description",
            resource_policy=default_project_resource_policy,
        )
        creator = Creator(spec=creator_spec)

        result = await group_repository_with_mock_role_manager.create(creator)

        assert result.name == "test-new-group"
        assert result.domain_name == test_domain
        assert result.description == "Test group description"
        assert result.is_active is True

    async def test_create_domain_not_exists(
        self,
        group_repository_with_mock_role_manager: GroupRepository,
        default_project_resource_policy: str,
    ) -> None:
        """Test group creation fails when domain does not exist"""
        creator_spec = GroupCreatorSpec(
            name="test-group",
            domain_name="nonexistent-domain",
            resource_policy=default_project_resource_policy,
        )
        creator = Creator(spec=creator_spec)

        with pytest.raises(InvalidAPIParameters):
            await group_repository_with_mock_role_manager.create(creator)

    async def test_create_duplicate_name_in_domain(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        group_repository_with_mock_role_manager: GroupRepository,
        test_domain: str,
        default_project_resource_policy: str,
    ) -> None:
        """Test group creation fails with duplicate name in same domain"""
        creator_spec = GroupCreatorSpec(
            name="duplicate-group",
            domain_name=test_domain,
            resource_policy=default_project_resource_policy,
        )

        # First creation succeeds
        await group_repository_with_mock_role_manager.create(Creator(spec=creator_spec))

        # Second creation with same name should fail
        with pytest.raises(InvalidAPIParameters):
            await group_repository_with_mock_role_manager.create(Creator(spec=creator_spec))

    # ===========================================
    # Tests for modify_validated method
    # ===========================================

    async def test_modify_validated_success(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        group_repository: GroupRepository,
        test_group: uuid.UUID,
    ) -> None:
        """Test successful group modification of name and description"""
        updater_spec = GroupUpdaterSpec(
            name=OptionalState.update("updated-group-name"),
            description=TriState.update("Updated description"),
        )
        updater = Updater(spec=updater_spec, pk_value=test_group)

        result = await group_repository.modify_validated(
            updater=updater,
        )

        assert result is not None
        assert result.name == "updated-group-name"
        assert result.description == "Updated description"

    async def test_modify_validated_group_not_found(
        self,
        group_repository: GroupRepository,
    ) -> None:
        """Test modification fails when group does not exist"""
        nonexistent_id = uuid.uuid4()
        updater_spec = GroupUpdaterSpec(
            description=TriState.update("New description"),
        )
        updater = Updater(spec=updater_spec, pk_value=nonexistent_id)

        with pytest.raises(ProjectNotFound):
            await group_repository.modify_validated(
                updater=updater,
            )

    async def test_modify_validated_add_users(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        group_repository: GroupRepository,
        test_group: uuid.UUID,
        test_users_for_group: list[uuid.UUID],
    ) -> None:
        """Test adding users to group with user_update_mode='add'"""
        updater_spec = GroupUpdaterSpec()
        updater = Updater(spec=updater_spec, pk_value=test_group)

        await group_repository.modify_validated(
            updater=updater,
            user_update_mode="add",
            user_uuids=test_users_for_group[:2],
        )

        # Verify users were added
        async with db_with_cleanup.begin_session() as session:
            assoc_result = await session.execute(
                sa.select(association_groups_users).where(
                    association_groups_users.c.group_id == test_group
                )
            )
            associations = assoc_result.fetchall()
            assert len(associations) == 2
            added_user_ids = {a.user_id for a in associations}
            assert test_users_for_group[0] in added_user_ids
            assert test_users_for_group[1] in added_user_ids

    async def test_modify_validated_remove_users(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        group_repository: GroupRepository,
        test_group: uuid.UUID,
        test_users_for_group: list[uuid.UUID],
    ) -> None:
        """Test removing users from group with user_update_mode='remove'"""
        updater_spec = GroupUpdaterSpec()
        updater = Updater(spec=updater_spec, pk_value=test_group)

        # First add all users
        await group_repository.modify_validated(
            updater=updater,
            user_update_mode="add",
            user_uuids=test_users_for_group,
        )

        # Then remove first user
        await group_repository.modify_validated(
            updater=updater,
            user_update_mode="remove",
            user_uuids=test_users_for_group[:1],
        )

        # Verify user was removed
        async with db_with_cleanup.begin_session() as session:
            assoc_result = await session.execute(
                sa.select(association_groups_users).where(
                    association_groups_users.c.group_id == test_group
                )
            )
            associations = assoc_result.fetchall()
            assert len(associations) == 2  # 3 added - 1 removed = 2
            remaining_user_ids = {a.user_id for a in associations}
            assert test_users_for_group[0] not in remaining_user_ids
            assert test_users_for_group[1] in remaining_user_ids
            assert test_users_for_group[2] in remaining_user_ids

    # ===========================================
    # Tests for mark_inactive method
    # ===========================================

    async def test_mark_inactive_success(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        group_repository: GroupRepository,
        test_group: uuid.UUID,
    ) -> None:
        """Test successful group soft deletion sets is_active=False and integration_id=None"""
        # Verify initial state
        async with db_with_cleanup.begin_session() as session:
            group_row = await session.scalar(sa.select(GroupRow).where(GroupRow.id == test_group))
            assert group_row is not None
            assert group_row.is_active is True
            assert group_row.integration_id == "test-integration-id"

        await group_repository.mark_inactive(test_group)

        # Verify group is marked inactive
        async with db_with_cleanup.begin_session() as session:
            group_row = await session.scalar(sa.select(GroupRow).where(GroupRow.id == test_group))
            assert group_row is not None
            assert group_row.is_active is False
            assert group_row.integration_id is None

    async def test_mark_inactive_group_not_found(
        self,
        group_repository: GroupRepository,
    ) -> None:
        """Test mark_inactive fails when group does not exist"""
        nonexistent_id = uuid.uuid4()

        with pytest.raises(ProjectNotFound):
            await group_repository.mark_inactive(nonexistent_id)

    # ===========================================
    # Tests for purge_group method
    # ===========================================

    async def test_purge_group_success(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        group_repository: GroupRepository,
        test_group: uuid.UUID,
    ) -> None:
        """Test successful group purge (hard delete)"""
        result = await group_repository.purge_group(test_group)

        assert result is True

        # Verify group is completely deleted
        async with db_with_cleanup.begin_session() as session:
            group_row = await session.scalar(sa.select(GroupRow).where(GroupRow.id == test_group))
            assert group_row is None

    async def test_purge_group_with_active_kernels(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        group_repository: GroupRepository,
        group_with_active_kernel: uuid.UUID,
    ) -> None:
        """Test purge fails when group has active kernels"""
        with pytest.raises(ProjectHasActiveKernelsError):
            await group_repository.purge_group(group_with_active_kernel)

        # Verify group still exists
        async with db_with_cleanup.begin_session() as session:
            group_row = await session.scalar(
                sa.select(GroupRow).where(GroupRow.id == group_with_active_kernel)
            )
            assert group_row is not None

    async def test_purge_group_with_active_endpoints(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        group_repository: GroupRepository,
        group_with_active_endpoint: uuid.UUID,
    ) -> None:
        """Test purge fails when group has active endpoints"""
        with pytest.raises(ProjectHasActiveEndpointsError):
            await group_repository.purge_group(group_with_active_endpoint)

        # Verify group still exists
        async with db_with_cleanup.begin_session() as session:
            group_row = await session.scalar(
                sa.select(GroupRow).where(GroupRow.id == group_with_active_endpoint)
            )
            assert group_row is not None

    async def test_purge_group_with_mounted_vfolders(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        group_repository: GroupRepository,
        group_with_mounted_vfolders: uuid.UUID,
    ) -> None:
        """Test purge fails when group has vfolders mounted to active kernels"""
        with pytest.raises(ProjectHasVFoldersMountedError):
            await group_repository.purge_group(group_with_mounted_vfolders)

        # Verify group still exists
        async with db_with_cleanup.begin_session() as session:
            group_row = await session.scalar(
                sa.select(GroupRow).where(GroupRow.id == group_with_mounted_vfolders)
            )
            assert group_row is not None


class TestGroupRowVFolderHostPermissionMap:
    """Tests for VFolderHostPermissionMap type handling in GroupRow"""

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        """Database connection with tables created."""
        async with with_tables(
            database_connection,
            [
                DomainRow,
                ProjectResourcePolicyRow,
                GroupRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def test_domain(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
        """Create test domain."""
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
    async def project_resource_policy(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
        """Create a project resource policy."""
        policy_name = f"test-policy-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as session:
            policy = ProjectResourcePolicyRow(
                name=policy_name,
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_network_count=3,
            )
            session.add(policy)
            await session.commit()

        return policy_name

    @pytest.fixture
    async def test_group(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain: str,
        project_resource_policy: str,
    ) -> uuid.UUID:
        """Create a group with allowed_vfolder_hosts set."""
        group_id = uuid.uuid4()

        async with db_with_cleanup.begin_session() as session:
            group = GroupRow(
                id=group_id,
                name=f"test-group-{group_id.hex[:8]}",
                description="Test group with vfolder hosts",
                is_active=True,
                domain_name=test_domain,
                total_resource_slots={},
                allowed_vfolder_hosts={
                    "local": ["create-vfolder", "mount-in-session"],
                },
                integration_id=None,
                resource_policy=project_resource_policy,
                type=ProjectType.GENERAL,
            )
            session.add(group)
            await session.commit()

        return group_id

    async def test_group_row_allowed_vfolder_hosts_is_dict(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_group: uuid.UUID,
    ) -> None:
        """Test that GroupRow.allowed_vfolder_hosts is dict type."""
        async with db_with_cleanup.begin_session() as session:
            group_row = await session.scalar(sa.select(GroupRow).where(GroupRow.id == test_group))
            assert group_row is not None
            assert isinstance(group_row.allowed_vfolder_hosts, VFolderHostPermissionMap)

    async def test_group_data_allowed_vfolder_hosts_is_vfolder_host_permission_map(
        self,
        test_domain: str,
        project_resource_policy: str,
    ) -> None:
        """Test that GroupRow.to_data() properly converts allowed_vfolder_hosts to enums.

        This tests the create path (not DB read path) where allowed_vfolder_hosts
        is passed as string lists. GroupRow.to_data() should convert strings to
        VFolderHostPermission enums. If not converted, to_json() will fail with
        "'str' object has no attribute 'value'".

        Note: DB read path is already handled by VFolderHostPermissionColumn.process_result_value()
        which returns sets of enums. This test verifies the create path works correctly.
        """
        # Create GroupRow directly without DB (simulates create path)
        group_row = GroupRow(
            id=uuid.uuid4(),
            name="test-group",
            description="Test group",
            is_active=True,
            domain_name=test_domain,
            total_resource_slots={},
            # String lists as passed from GroupCreatorSpec
            allowed_vfolder_hosts=VFolderHostPermissionMap({
                "local": {VFolderHostPermission.CREATE, VFolderHostPermission.MOUNT_IN_SESSION},
            }),
            integration_id=None,
            resource_policy=project_resource_policy,
            type=ProjectType.GENERAL,
        )

        group_data = group_row.to_data()
        assert isinstance(group_data.allowed_vfolder_hosts, VFolderHostPermissionMap)

        # Verify values are VFolderHostPermission enums, not strings
        for host, perms in group_data.allowed_vfolder_hosts.items():
            for perm in perms:
                assert isinstance(perm, VFolderHostPermission), (
                    f"allowed_vfolder_hosts['{host}'] contains {type(perm).__name__} "
                    f"instead of VFolderHostPermission enum"
                )

    async def test_group_data_allowed_vfolder_hosts_values_are_sets(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_group: uuid.UUID,
    ) -> None:
        """Test that GroupData.allowed_vfolder_hosts values are sets of VFolderHostPermission.

        VFolderHostPermissionColumn.process_result_value() returns sets, so the values
        in allowed_vfolder_hosts should be sets, not lists.
        """
        async with db_with_cleanup.begin_session() as session:
            group_row = await session.scalar(sa.select(GroupRow).where(GroupRow.id == test_group))
            assert group_row is not None

            group_data = group_row.to_data()

            # Values should be sets (from VFolderHostPermissionColumn)
            for host, perms in group_data.allowed_vfolder_hosts.items():
                assert isinstance(perms, set), (
                    f"allowed_vfolder_hosts['{host}'] should be a set, got {type(perms).__name__}"
                )

    async def test_group_data_allowed_vfolder_hosts_to_json_is_serializable(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_group: uuid.UUID,
    ) -> None:
        """Test that GroupData.allowed_vfolder_hosts.to_json() returns JSON-serializable data.

        Since allowed_vfolder_hosts values are sets (not JSON serializable),
        calling .to_json() should convert them to lists for proper serialization.
        """

        async with db_with_cleanup.begin_session() as session:
            group_row = await session.scalar(sa.select(GroupRow).where(GroupRow.id == test_group))
            assert group_row is not None

            group_data = group_row.to_data()
            json_data = group_data.allowed_vfolder_hosts.to_json()

            # Should be JSON serializable without error
            try:
                json.dumps(json_data)
            except TypeError as e:
                pytest.fail(f"to_json() result is not JSON serializable: {e}")
