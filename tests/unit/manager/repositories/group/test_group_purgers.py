"""
Tests for group purgers functionality.
Tests the purger pattern implementation for group-related deletions.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING

import pytest
import sqlalchemy as sa

from ai.backend.common.types import ResourceSlot
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.model_serving.types import RuntimeVariant

# Import Row classes to ensure SQLAlchemy mapper initialization
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.endpoint import EndpointLifecycle, EndpointRow
from ai.backend.manager.models.group import GroupRow, ProjectType
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.image import ImageRow  # noqa: F401
from ai.backend.manager.models.kernel.row import KernelRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.routing.row import RouteStatus, RoutingRow
from ai.backend.manager.models.scaling_group import ScalingGroupOpts, ScalingGroupRow
from ai.backend.manager.models.session import SessionRow, SessionStatus, SessionTypes
from ai.backend.manager.models.user import UserRole, UserRow, UserStatus
from ai.backend.manager.models.vfolder.row import VFolderRow
from ai.backend.manager.repositories.base.purger import BatchPurger, execute_batch_purger
from ai.backend.manager.repositories.group.purgers import (
    GroupBatchPurgerSpec,
    GroupEndpointBatchPurgerSpec,
    GroupKernelBatchPurgerSpec,
    GroupSessionBatchPurgerSpec,
    SessionByIdsBatchPurgerSpec,
)
from ai.backend.testutils.db import with_tables

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


class TestGroupPurgersIntegration:
    """Integration tests for group purgers with real database."""

    @pytest.fixture
    async def db_with_cleanup(
        self, database_connection: ExtendedAsyncSAEngine
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
                # FK dependency order: parents before children
                DomainRow,
                ProjectResourcePolicyRow,
                UserResourcePolicyRow,
                KeyPairResourcePolicyRow,
                ScalingGroupRow,
                UserRow,
                KeyPairRow,
                GroupRow,
                SessionRow,
                AgentRow,
                KernelRow,
                VFolderRow,
                EndpointRow,
                RoutingRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def sample_domain(self, db_with_cleanup: ExtendedAsyncSAEngine) -> str:
        """Create a test domain."""
        domain_name = f"test-domain-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as session:
            domain = DomainRow(
                name=domain_name,
                description=f"Test domain {domain_name}",
                is_active=True,
                total_resource_slots={},
                allowed_vfolder_hosts={},
                allowed_docker_registries=[],
                dotfiles=b"",
                integration_id=None,
            )
            session.add(domain)
        return domain_name

    @pytest.fixture
    async def project_resource_policy(self, db_with_cleanup: ExtendedAsyncSAEngine) -> str:
        """Create a project resource policy."""
        policy_name = f"project-policy-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as session:
            policy = ProjectResourcePolicyRow(
                name=policy_name,
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_network_count=3,
            )
            session.add(policy)
        return policy_name

    @pytest.fixture
    async def user_resource_policy(self, db_with_cleanup: ExtendedAsyncSAEngine) -> str:
        """Create a user resource policy."""
        policy_name = f"user-policy-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as session:
            policy = UserResourcePolicyRow(
                name=policy_name,
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_session_count_per_model_session=10,
                max_customized_image_count=10,
            )
            session.add(policy)
        return policy_name

    @pytest.fixture
    async def sample_user(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_domain: str,
        user_resource_policy: str,
    ) -> UserRow:
        """Create a test user."""
        user_uuid = uuid.uuid4()
        password_info = PasswordInfo(
            password="test_password",
            algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
            rounds=100_000,
            salt_size=32,
        )
        async with db_with_cleanup.begin_session() as session:
            user = UserRow(
                uuid=user_uuid,
                username=f"testuser-{uuid.uuid4().hex[:8]}",
                email=f"test-{uuid.uuid4().hex[:8]}@example.com",
                password=password_info,
                need_password_change=False,
                full_name="Test User",
                description="Test user for integration tests",
                status=UserStatus.ACTIVE,
                status_info="",
                domain_name=sample_domain,
                role=UserRole.USER,
                resource_policy=user_resource_policy,
            )
            session.add(user)
            await session.flush()
            await session.refresh(user)
            return user

    @pytest.fixture
    async def sample_group(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_domain: str,
        project_resource_policy: str,
    ) -> GroupRow:
        """Create a test group."""
        group_id = uuid.uuid4()
        async with db_with_cleanup.begin_session() as session:
            group = GroupRow(
                id=group_id,
                name=f"test-group-{uuid.uuid4().hex[:8]}",
                description="Test group for integration tests",
                is_active=True,
                domain_name=sample_domain,
                total_resource_slots={},
                allowed_vfolder_hosts={},
                dotfiles=b"\x90",
                resource_policy=project_resource_policy,
                type=ProjectType.GENERAL,
            )
            session.add(group)
            await session.flush()
            await session.refresh(group)
            return group

    @pytest.fixture
    async def sample_scaling_group(self, db_with_cleanup: ExtendedAsyncSAEngine) -> str:
        """Create a test scaling group."""
        sgroup_name = f"test-sgroup-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as session:
            sgroup = ScalingGroupRow(
                name=sgroup_name,
                driver="static",
                driver_opts={},
                scheduler="fifo",
                scheduler_opts=ScalingGroupOpts(),
            )
            session.add(sgroup)
        return sgroup_name

    @pytest.fixture
    async def sample_sessions(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_group: GroupRow,
        sample_domain: str,
        sample_user: UserRow,
    ) -> list[SessionRow]:
        """Create test sessions belonging to the group."""
        sessions: list[SessionRow] = []
        async with db_with_cleanup.begin_session() as session:
            for i in range(3):
                sess = SessionRow(
                    name=f"test-session-{i}-{uuid.uuid4().hex[:8]}",
                    session_type=SessionTypes.INTERACTIVE,
                    cluster_mode="single-node",
                    cluster_size=1,
                    domain_name=sample_domain,
                    group_id=sample_group.id,
                    user_uuid=sample_user.uuid,
                    occupying_slots=ResourceSlot({}),
                    requested_slots=ResourceSlot({}),
                    status=SessionStatus.TERMINATED,
                    status_info="",
                    target_sgroup_names=[],
                    vfolder_mounts=[],
                    environ={},
                )
                session.add(sess)
                sessions.append(sess)
            await session.flush()
            for sess in sessions:
                await session.refresh(sess)
        return sessions

    @pytest.fixture
    async def sample_kernels(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_sessions: list[SessionRow],
        sample_domain: str,
        sample_group: GroupRow,
        sample_user: UserRow,
    ) -> list[KernelRow]:
        """Create test kernels belonging to sessions."""
        kernels: list[KernelRow] = []
        async with db_with_cleanup.begin_session() as session:
            for sess in sample_sessions:
                kernel = KernelRow(
                    session_id=sess.id,
                    domain_name=sample_domain,
                    group_id=sample_group.id,
                    user_uuid=sample_user.uuid,
                    occupied_slots=ResourceSlot({}),
                    requested_slots=ResourceSlot({}),
                    occupied_shares={},
                    vfolder_mounts=[],
                    status=KernelStatus.TERMINATED,
                    repl_in_port=0,
                    repl_out_port=0,
                    stdin_port=0,
                    stdout_port=0,
                )
                session.add(kernel)
                kernels.append(kernel)
            await session.flush()
            for kernel in kernels:
                await session.refresh(kernel)
        return kernels

    @pytest.fixture
    async def sample_endpoints(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_domain: str,
        sample_group: GroupRow,
        sample_user: UserRow,
        sample_scaling_group: str,
    ) -> list[EndpointRow]:
        """Create test endpoints belonging to the group."""
        endpoints: list[EndpointRow] = []
        async with db_with_cleanup.begin_session() as session:
            for i in range(3):
                endpoint = EndpointRow(
                    name=f"test-endpoint-{i}-{uuid.uuid4().hex[:8]}",
                    created_user=sample_user.uuid,
                    session_owner=sample_user.uuid,
                    domain=sample_domain,
                    project=sample_group.id,
                    resource_group=sample_scaling_group,
                    lifecycle_stage=EndpointLifecycle.DESTROYED,
                    replicas=0,
                    model_mount_destination="/models",
                    cluster_mode="single-node",
                    cluster_size=1,
                    runtime_variant=RuntimeVariant.CUSTOM,
                    resource_slots=ResourceSlot({}),
                )
                session.add(endpoint)
                endpoints.append(endpoint)
            await session.flush()
            for endpoint in endpoints:
                await session.refresh(endpoint)
        return endpoints

    @pytest.fixture
    async def sample_endpoint_sessions_with_routings(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_endpoints: list[EndpointRow],
        sample_domain: str,
        sample_group: GroupRow,
        sample_user: UserRow,
    ) -> tuple[list[SessionRow], list[RoutingRow]]:
        """Create test sessions connected to endpoints via routings."""
        sessions: list[SessionRow] = []
        routings: list[RoutingRow] = []
        async with db_with_cleanup.begin_session() as session:
            for i, endpoint in enumerate(sample_endpoints):
                # Create a session for this endpoint
                sess = SessionRow(
                    name=f"endpoint-session-{i}-{uuid.uuid4().hex[:8]}",
                    session_type=SessionTypes.INFERENCE,
                    cluster_mode="single-node",
                    cluster_size=1,
                    domain_name=sample_domain,
                    group_id=sample_group.id,
                    user_uuid=sample_user.uuid,
                    occupying_slots=ResourceSlot({}),
                    requested_slots=ResourceSlot({}),
                    status=SessionStatus.TERMINATED,
                    status_info="",
                    target_sgroup_names=[],
                    vfolder_mounts=[],
                    environ={},
                )
                session.add(sess)
                await session.flush()
                await session.refresh(sess)
                sessions.append(sess)

                # Create routing connecting endpoint to session
                routing = RoutingRow(
                    id=uuid.uuid4(),
                    endpoint=endpoint.id,
                    session=sess.id,
                    session_owner=sample_user.uuid,
                    domain=sample_domain,
                    project=sample_group.id,
                    status=RouteStatus.TERMINATED,
                    traffic_ratio=1.0,
                )
                session.add(routing)
                routings.append(routing)
            await session.flush()
            for routing in routings:
                await session.refresh(routing)
        return sessions, routings

    @pytest.mark.asyncio
    async def test_purge_group_sessions(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_group: GroupRow,
        sample_sessions: list[SessionRow],
    ) -> None:
        """Test purging sessions belonging to a group."""
        group_id = sample_group.id

        # Verify sessions exist
        async with db_with_cleanup.begin_session() as session:
            count = await session.scalar(
                sa.select(sa.func.count())
                .select_from(SessionRow)
                .where(SessionRow.group_id == group_id)
            )
            assert count == len(sample_sessions)

        # Purge sessions
        async with db_with_cleanup.begin_session() as session:
            purger = BatchPurger(spec=GroupSessionBatchPurgerSpec(group_id=group_id))
            result = await execute_batch_purger(session, purger)
            assert result.deleted_count == len(sample_sessions)

        # Verify sessions are deleted
        async with db_with_cleanup.begin_session() as session:
            count = await session.scalar(
                sa.select(sa.func.count())
                .select_from(SessionRow)
                .where(SessionRow.group_id == group_id)
            )
            assert count == 0

    @pytest.mark.asyncio
    async def test_purge_group_kernels(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_sessions: list[SessionRow],
        sample_kernels: list[KernelRow],
        sample_group: GroupRow,
    ) -> None:
        """Test purging kernels belonging to group sessions."""
        group_id = sample_group.id
        session_ids = [sess.id for sess in sample_sessions]

        # Verify kernels exist
        async with db_with_cleanup.begin_session() as session:
            count = await session.scalar(
                sa.select(sa.func.count())
                .select_from(KernelRow)
                .where(KernelRow.session_id.in_(session_ids))
            )
            assert count == len(sample_kernels)

        # Purge kernels
        async with db_with_cleanup.begin_session() as session:
            purger = BatchPurger(spec=GroupKernelBatchPurgerSpec(group_id=group_id))
            result = await execute_batch_purger(session, purger)
            assert result.deleted_count == len(sample_kernels)

        # Verify kernels are deleted
        async with db_with_cleanup.begin_session() as session:
            count = await session.scalar(
                sa.select(sa.func.count())
                .select_from(KernelRow)
                .where(KernelRow.session_id.in_(session_ids))
            )
            assert count == 0

    @pytest.mark.asyncio
    async def test_purge_group_endpoints(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_endpoints: list[EndpointRow],
        sample_group: GroupRow,
    ) -> None:
        """Test purging endpoints belonging to the group."""
        group_id = sample_group.id

        # Verify endpoints exist
        async with db_with_cleanup.begin_session() as session:
            count = await session.scalar(
                sa.select(sa.func.count())
                .select_from(EndpointRow)
                .where(EndpointRow.project == group_id)
            )
            assert count == len(sample_endpoints)

        # Purge endpoints
        async with db_with_cleanup.begin_session() as session:
            purger = BatchPurger(spec=GroupEndpointBatchPurgerSpec(project_id=group_id))
            result = await execute_batch_purger(session, purger)
            assert result.deleted_count == len(sample_endpoints)

        # Verify endpoints are deleted
        async with db_with_cleanup.begin_session() as session:
            count = await session.scalar(
                sa.select(sa.func.count())
                .select_from(EndpointRow)
                .where(EndpointRow.project == group_id)
            )
            assert count == 0

    @pytest.mark.asyncio
    async def test_purge_group_endpoint_sessions(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_endpoint_sessions_with_routings: tuple[list[SessionRow], list[RoutingRow]],
        sample_endpoints: list[EndpointRow],
        sample_group: GroupRow,
    ) -> None:
        """Test purging sessions connected to group endpoints via routings.

        The correct deletion order is:
        1. Collect session IDs (before routings are deleted)
        2. Delete endpoints (CASCADE deletes routings)
        3. Delete sessions by collected IDs (now safe because routings are gone)
        """
        group_id = sample_group.id
        endpoint_sessions, _ = sample_endpoint_sessions_with_routings
        session_ids = [sess.id for sess in endpoint_sessions]

        # Verify endpoint sessions exist
        async with db_with_cleanup.begin_session() as session:
            count = await session.scalar(
                sa.select(sa.func.count())
                .select_from(SessionRow)
                .where(SessionRow.id.in_(session_ids))
            )
            assert count == len(endpoint_sessions)

        # Delete endpoints first (CASCADE deletes routings)
        async with db_with_cleanup.begin_session() as session:
            purger = BatchPurger(spec=GroupEndpointBatchPurgerSpec(project_id=group_id))
            result = await execute_batch_purger(session, purger)
            assert result.deleted_count == len(sample_endpoints)

        # Purge endpoint sessions using collected session IDs
        async with db_with_cleanup.begin_session() as session:
            purger = BatchPurger(spec=SessionByIdsBatchPurgerSpec(session_ids=session_ids))
            result = await execute_batch_purger(session, purger)
            assert result.deleted_count == len(endpoint_sessions)

        # Verify endpoint sessions are deleted
        async with db_with_cleanup.begin_session() as session:
            count = await session.scalar(
                sa.select(sa.func.count())
                .select_from(SessionRow)
                .where(SessionRow.id.in_(session_ids))
            )
            assert count == 0

    @pytest.mark.asyncio
    async def test_purge_group(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_group: GroupRow,
    ) -> None:
        """Test purging the group itself."""
        group_id = sample_group.id

        # Verify group exists
        async with db_with_cleanup.begin_session() as session:
            count = await session.scalar(
                sa.select(sa.func.count()).select_from(GroupRow).where(GroupRow.id == group_id)
            )
            assert count == 1

        # Purge group
        async with db_with_cleanup.begin_session() as session:
            purger = BatchPurger(spec=GroupBatchPurgerSpec(group_id=group_id), batch_size=1)
            result = await execute_batch_purger(session, purger)
            assert result.deleted_count == 1

        # Verify group is deleted
        async with db_with_cleanup.begin_session() as session:
            count = await session.scalar(
                sa.select(sa.func.count()).select_from(GroupRow).where(GroupRow.id == group_id)
            )
            assert count == 0
