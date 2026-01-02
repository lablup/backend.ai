"""
Tests for session termination functionality in ScheduleRepository.
Tests the repository layer with real database operations using fixtures.
"""

import uuid
from collections.abc import AsyncGenerator
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
import sqlalchemy as sa
from dateutil.tz import tzutc

from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.types import (
    AccessKey,
    AgentId,
    AgentSelectionStrategy,
    ClusterMode,
    ResourceSlot,
    SessionId,
    SessionResult,
    SessionTypes,
)
from ai.backend.manager.config.loader.legacy_etcd_loader import LegacyEtcdLoader
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.agent.types import AgentStatus
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.data.user.types import UserRole
from ai.backend.manager.models import (
    AgentRow,
    DomainRow,
    GroupRow,
    KernelRow,
    KeyPairResourcePolicyRow,
    KeyPairRow,
    ProjectResourcePolicyRow,
    ScalingGroupOpts,
    ScalingGroupRow,
    SessionRow,
    UserResourcePolicyRow,
    UserRow,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.schedule.repository import (
    KernelTerminationResult,
    MarkTerminatingResult,
    ScheduleRepository,
    SessionTerminationResult,
    TerminatingKernelData,
    TerminatingSessionData,
)
from ai.backend.testutils.db import with_tables


@pytest.fixture
async def db_with_cleanup(
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
            AgentRow,
            SessionRow,
            KernelRow,
        ],
    ):
        yield database_connection


@pytest.fixture
async def sample_domain_and_policies(
    db_with_cleanup: ExtendedAsyncSAEngine,
) -> AsyncGenerator[dict[str, Any], None]:
    """Create sample domain and resource policies for testing"""
    data: dict[str, Any] = {}

    async with db_with_cleanup.begin_session() as db_sess:
        # Create domain
        domain = DomainRow(
            name="test-termination-domain",
            total_resource_slots=ResourceSlot({"cpu": Decimal("1000"), "mem": Decimal("1048576")}),
        )
        db_sess.add(domain)
        data["domain"] = domain

        # Create policies
        user_policy = UserResourcePolicyRow(
            name="test-termination-policy",
            max_vfolder_count=10,
            max_quota_scope_size=-1,
            max_session_count_per_model_session=10,
            max_customized_image_count=10,
        )
        db_sess.add(user_policy)
        data["user_policy"] = user_policy

        project_policy = ProjectResourcePolicyRow(
            name="test-termination-policy",
            max_vfolder_count=10,
            max_quota_scope_size=-1,
            max_network_count=10,
        )
        db_sess.add(project_policy)
        data["project_policy"] = project_policy

        kp_policy = KeyPairResourcePolicyRow(
            name="test-termination-policy",
            total_resource_slots=ResourceSlot({"cpu": Decimal("100"), "mem": Decimal("102400")}),
            max_concurrent_sessions=10,
            max_concurrent_sftp_sessions=2,
            max_pending_session_count=5,
            max_pending_session_resource_slots=ResourceSlot({
                "cpu": Decimal("50"),
                "mem": Decimal("51200"),
            }),
            max_containers_per_session=10,
            idle_timeout=3600,
        )
        db_sess.add(kp_policy)
        data["kp_policy"] = kp_policy

        await db_sess.commit()

    yield data


@pytest.fixture
async def sample_scaling_group_and_agent(
    db_with_cleanup: ExtendedAsyncSAEngine,
) -> AsyncGenerator[dict[str, Any], None]:
    """Create sample scaling group and agent for testing"""
    data: dict[str, Any] = {}

    async with db_with_cleanup.begin_session() as db_sess:
        # Create scaling group
        sg = ScalingGroupRow(
            name="test-termination-sgroup",
            driver="test-driver",
            scheduler="fifo",
            scheduler_opts=ScalingGroupOpts(
                allowed_session_types=[SessionTypes.INTERACTIVE, SessionTypes.BATCH],
                pending_timeout=timedelta(seconds=300),
                agent_selection_strategy=AgentSelectionStrategy.ROUNDROBIN,
            ),
            driver_opts={},
            use_host_network=False,
            is_active=True,
        )
        db_sess.add(sg)
        data["scaling_group"] = sg

        # Create agent
        agent = AgentRow(
            id=AgentId("test-agent-termination"),
            status=AgentStatus.ALIVE,
            status_changed=datetime.now(tzutc()),
            region="test-region",
            scaling_group=sg.name,
            schedulable=True,
            available_slots=ResourceSlot({"cpu": Decimal("16.0"), "mem": Decimal("32768")}),
            occupied_slots=ResourceSlot({"cpu": Decimal("4.0"), "mem": Decimal("8192")}),
            addr="10.0.0.1:2001",
            architecture="x86_64",
            version="24.03.0",
        )
        db_sess.add(agent)
        data["agent"] = agent

        await db_sess.commit()

    yield data


@pytest.fixture
async def sample_user_and_keypair(
    db_with_cleanup: ExtendedAsyncSAEngine,
    sample_domain_and_policies: dict[str, Any],
) -> AsyncGenerator[dict[str, Any], None]:
    """Create sample user, group, and keypair for testing"""
    data: dict[str, Any] = {}
    domain = sample_domain_and_policies["domain"]

    async with db_with_cleanup.begin_session() as db_sess:
        # Create group
        group = GroupRow(
            id=uuid.uuid4(),
            name="test-termination-group",
            domain_name=domain.name,
            total_resource_slots=ResourceSlot({"cpu": Decimal("500"), "mem": Decimal("524288")}),
            resource_policy="test-termination-policy",
        )
        db_sess.add(group)
        data["group"] = group

        # Create user
        from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
        from ai.backend.manager.models.hasher.types import PasswordInfo

        password_info = PasswordInfo(
            password="dummy",
            algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
            rounds=600_000,
            salt_size=32,
        )

        user = UserRow(
            uuid=uuid.uuid4(),
            username="test-termination-user",
            email="termination@example.com",
            password=password_info,
            domain_name=domain.name,
            role=UserRole.USER,
            resource_policy="test-termination-policy",
        )
        db_sess.add(user)
        data["user"] = user

        await db_sess.commit()

        # Create keypair
        keypair = KeyPairRow(
            access_key=AccessKey("test-termination-key"),
            secret_key="dummy-secret",
            user_id=user.email,
            user=user.uuid,
            is_active=True,
            resource_policy="test-termination-policy",
        )
        db_sess.add(keypair)
        data["keypair"] = keypair

        await db_sess.commit()

    yield data


@pytest.fixture
async def sample_sessions_for_termination(
    db_with_cleanup: ExtendedAsyncSAEngine,
    sample_domain_and_policies: dict[str, Any],
    sample_scaling_group_and_agent: dict[str, Any],
    sample_user_and_keypair: dict[str, Any],
) -> AsyncGenerator[dict[str, Any], None]:
    """Create sample sessions with various states for termination testing"""
    data: dict[str, Any] = {
        "sessions": [],
        "kernels": [],
    }

    domain = sample_domain_and_policies["domain"]
    sg = sample_scaling_group_and_agent["scaling_group"]
    agent = sample_scaling_group_and_agent["agent"]
    group = sample_user_and_keypair["group"]
    user = sample_user_and_keypair["user"]
    keypair = sample_user_and_keypair["keypair"]

    async with db_with_cleanup.begin_session() as db_sess:
        # Session states to test
        session_configs = [
            (SessionStatus.PENDING, None, None),  # Pending session - should be CANCELLED
            (SessionStatus.PULLING, agent.id, None),  # Pulling session - should be CANCELLED
            (
                SessionStatus.RUNNING,
                agent.id,
                "container-1",
            ),  # Running session - should be TERMINATING
            (SessionStatus.TERMINATING, agent.id, "container-2"),  # Already terminating
            (SessionStatus.TERMINATED, agent.id, "container-3"),  # Already terminated
        ]

        for i, (status, agent_id, container_id) in enumerate(session_configs):
            # Create session
            session = SessionRow(
                id=SessionId(uuid.uuid4()),
                name=f"test-termination-session-{i}",
                session_type=SessionTypes.INTERACTIVE,
                domain_name=domain.name,
                group_id=group.id,
                user_uuid=user.uuid,
                access_key=keypair.access_key,
                scaling_group_name=sg.name,
                status=status,
                status_info="",  # Will be updated when marked for termination
                cluster_mode=ClusterMode.SINGLE_NODE,
                requested_slots=ResourceSlot({"cpu": Decimal("2"), "mem": Decimal("4096")}),
                created_at=datetime.now(tzutc()),
                images=["python:3.8"],
                vfolder_mounts=[],
                environ={},
                result=SessionResult.UNDEFINED,
            )
            db_sess.add(session)
            data["sessions"].append(session)

            # Create kernel for each session
            kernel_status = {
                SessionStatus.PENDING: KernelStatus.PENDING,
                SessionStatus.PULLING: KernelStatus.PULLING,
                SessionStatus.RUNNING: KernelStatus.RUNNING,
                SessionStatus.TERMINATING: KernelStatus.TERMINATING,
                SessionStatus.TERMINATED: KernelStatus.TERMINATED,
            }[status]

            kernel = KernelRow(
                id=uuid.uuid4(),
                session_id=session.id,
                access_key=keypair.access_key,
                agent=agent_id,
                agent_addr=agent.addr if agent_id else None,
                scaling_group=sg.name,
                cluster_idx=0,
                cluster_role="main",
                cluster_hostname=f"kernel-{i}",
                image="python:3.8",
                architecture="x86_64",
                registry="docker.io",
                container_id=container_id,
                status=kernel_status,
                status_changed=datetime.now(tzutc()),
                occupied_slots=ResourceSlot({"cpu": Decimal("2"), "mem": Decimal("4096")}),
                requested_slots=ResourceSlot({"cpu": Decimal("2"), "mem": Decimal("4096")}),
                domain_name=domain.name,
                group_id=group.id,
                user_uuid=user.uuid,
                mounts=[],
                environ={},
                vfolder_mounts=[],
                preopen_ports=[],
                repl_in_port=2001,
                repl_out_port=2002,
                stdin_port=2003,
                stdout_port=2004,
            )
            db_sess.add(kernel)
            data["kernels"].append(kernel)

        await db_sess.commit()

    yield data


@pytest.fixture
def mock_valkey_stat_client() -> ValkeyStatClient:
    """Create mock Valkey stat client"""
    mock_client = MagicMock(spec=ValkeyStatClient)
    mock_client.get_keypair_concurrency_used = AsyncMock(return_value=2)
    mock_client._get_raw = AsyncMock(return_value=b"1")
    return mock_client


@pytest.fixture
def mock_config_provider() -> ManagerConfigProvider:
    """Create mock config provider"""
    mock_provider = MagicMock(spec=ManagerConfigProvider)
    mock_legacy_loader = MagicMock(spec=LegacyEtcdLoader)
    mock_legacy_loader.get_resource_slots = AsyncMock(return_value={"cpu": "count", "mem": "bytes"})
    mock_legacy_loader.get_raw = AsyncMock(return_value="10")
    mock_provider.legacy_etcd_config_loader = mock_legacy_loader
    return mock_provider


@pytest.fixture
async def schedule_repository(
    db_with_cleanup: ExtendedAsyncSAEngine,
    mock_valkey_stat_client: ValkeyStatClient,
    mock_config_provider: ManagerConfigProvider,
) -> ScheduleRepository:
    """Create ScheduleRepository instance"""
    return ScheduleRepository(
        db=db_with_cleanup,
        valkey_stat=mock_valkey_stat_client,
        config_provider=mock_config_provider,
    )


class TestSessionTermination:
    """Test cases for session termination functionality"""

    async def test_mark_sessions_terminating_various_states(
        self,
        schedule_repository: ScheduleRepository,
        sample_sessions_for_termination: dict[str, Any],
    ):
        """Test marking sessions for termination with various initial states"""
        sessions = sample_sessions_for_termination["sessions"]
        session_ids = [str(s.id) for s in sessions]

        # Mark all sessions for termination
        result = await schedule_repository.mark_sessions_terminating(
            session_ids,
            reason="TEST_TERMINATION",
        )

        # Verify the result categorization
        assert isinstance(result, MarkTerminatingResult)

        # Sessions 0, 1 (PENDING, PULLING) should be cancelled
        assert len(result.cancelled_sessions) == 2
        assert str(sessions[0].id) in result.cancelled_sessions
        assert str(sessions[1].id) in result.cancelled_sessions

        # Session 2 (RUNNING) should be marked as terminating
        assert len(result.terminating_sessions) == 1
        assert str(sessions[2].id) in result.terminating_sessions

        # Sessions 3, 4 (TERMINATING, TERMINATED) should be skipped
        assert len(result.skipped_sessions) == 2
        assert str(sessions[3].id) in result.skipped_sessions
        assert str(sessions[4].id) in result.skipped_sessions

        # Verify total processed count
        assert result.processed_count() == 3  # 2 cancelled + 1 terminating
        assert result.has_processed() is True

    async def test_mark_sessions_terminating_updates_database(
        self,
        schedule_repository: ScheduleRepository,
        sample_sessions_for_termination: dict[str, Any],
        db_with_cleanup: ExtendedAsyncSAEngine,
    ):
        """Test that mark_sessions_terminating correctly updates database"""
        sessions = sample_sessions_for_termination["sessions"]

        # Mark only the running session for termination
        running_session = sessions[2]  # RUNNING status
        result = await schedule_repository.mark_sessions_terminating(
            [str(running_session.id)],
            reason="USER_REQUESTED",
        )

        assert len(result.terminating_sessions) == 1

        # Verify database updates
        async with db_with_cleanup.begin_readonly_session() as db_sess:
            # Check session status
            stmt = sa.select(SessionRow).where(SessionRow.id == running_session.id)
            updated_session = await db_sess.scalar(stmt)
            assert updated_session.status == SessionStatus.TERMINATING
            assert updated_session.status_info == "USER_REQUESTED"

            # Check kernel status
            stmt = sa.select(KernelRow).where(KernelRow.session_id == running_session.id)
            updated_kernel = await db_sess.scalar(stmt)
            assert updated_kernel.status == KernelStatus.TERMINATING

    async def test_get_terminating_sessions(
        self,
        schedule_repository: ScheduleRepository,
        sample_sessions_for_termination: dict[str, Any],
    ):
        """Test fetching terminating sessions"""
        sessions = sample_sessions_for_termination["sessions"]

        # Mark running session as terminating
        running_session = sessions[2]
        await schedule_repository.mark_sessions_terminating(
            [str(running_session.id)],
            reason="TEST_REASON",
        )

        # Fetch terminating sessions
        terminating_sessions = await schedule_repository.get_terminating_sessions()

        # Should include the newly marked session and the already terminating one
        assert len(terminating_sessions) == 2

        # Find our marked session
        target_id = str(running_session.id)
        marked_session = next(
            (s for s in terminating_sessions if str(s.session_id) == target_id), None
        )
        assert marked_session is not None
        assert isinstance(marked_session, TerminatingSessionData)
        assert marked_session.status_info == "TEST_REASON"
        assert len(marked_session.kernels) == 1

        # Verify kernel data
        kernel_data = marked_session.kernels[0]
        assert isinstance(kernel_data, TerminatingKernelData)
        assert kernel_data.agent_id == "test-agent-termination"
        assert kernel_data.container_id == "container-1"

    async def test_batch_update_terminated_status_all_success(
        self,
        schedule_repository: ScheduleRepository,
        sample_sessions_for_termination: dict[str, Any],
        db_with_cleanup: ExtendedAsyncSAEngine,
    ):
        """Test batch update with all kernels terminated successfully"""
        sessions = sample_sessions_for_termination["sessions"]

        # Mark running session as terminating
        running_session = sessions[2]
        await schedule_repository.mark_sessions_terminating(
            [str(running_session.id)],
            reason="TEST_TERMINATION",
        )

        # Create termination results with all kernels successful
        termination_results = [
            SessionTerminationResult(
                session_id=running_session.id,
                access_key=running_session.access_key,
                creation_id=running_session.creation_id,
                session_type=running_session.session_type,
                reason="TEST_TERMINATION",
                kernel_results=[
                    KernelTerminationResult(
                        kernel_id=str(sample_sessions_for_termination["kernels"][2].id),
                        agent_id=sample_sessions_for_termination["kernels"][2].agent,
                        occupied_slots=sample_sessions_for_termination["kernels"][2].occupied_slots,
                        success=True,
                    )
                ],
            )
        ]

        # Apply batch update
        await schedule_repository.batch_update_terminated_status(termination_results)

        # Verify database updates
        async with db_with_cleanup.begin_readonly_session() as db_sess:
            # Check session status
            stmt = sa.select(SessionRow).where(SessionRow.id == running_session.id)
            updated_session = await db_sess.scalar(stmt)
            assert updated_session.status == SessionStatus.TERMINATED
            # Result field is not updated by termination process currently

            # Check kernel status
            stmt = sa.select(KernelRow).where(KernelRow.session_id == running_session.id)
            updated_kernel = await db_sess.scalar(stmt)
            assert updated_kernel.status == KernelStatus.TERMINATED
            assert updated_kernel.terminated_at is not None

    async def test_batch_update_terminated_status_partial_failure(
        self,
        schedule_repository: ScheduleRepository,
        sample_sessions_for_termination: dict[str, Any],
        db_with_cleanup: ExtendedAsyncSAEngine,
    ):
        """Test batch update with some kernels failing to terminate"""
        sessions = sample_sessions_for_termination["sessions"]
        kernels = sample_sessions_for_termination["kernels"]

        # Mark running session as terminating
        running_session = sessions[2]
        running_kernel = kernels[2]
        await schedule_repository.mark_sessions_terminating(
            [str(running_session.id)],
            reason="TEST_PARTIAL",
        )

        # Create termination results with kernel failure
        termination_results = [
            SessionTerminationResult(
                session_id=running_session.id,
                access_key=running_session.access_key,
                session_type=running_session.session_type,
                creation_id=running_session.creation_id,
                reason="TEST_PARTIAL",
                kernel_results=[
                    KernelTerminationResult(
                        kernel_id=str(running_kernel.id),
                        agent_id=running_kernel.agent,
                        occupied_slots=running_kernel.occupied_slots,
                        success=False,
                        error="Agent communication failed",
                    )
                ],
            )
        ]

        # Apply batch update
        await schedule_repository.batch_update_terminated_status(termination_results)

        # Verify database state - session should remain TERMINATING
        async with db_with_cleanup.begin_readonly_session() as db_sess:
            # Session should still be TERMINATING due to failure
            stmt = sa.select(SessionRow).where(SessionRow.id == running_session.id)
            updated_session = await db_sess.scalar(stmt)
            assert updated_session.status == SessionStatus.TERMINATING

            # Kernel should still be TERMINATING
            stmt = sa.select(KernelRow).where(KernelRow.session_id == running_session.id)
            updated_kernel = await db_sess.scalar(stmt)
            assert updated_kernel.status == KernelStatus.TERMINATING
            assert updated_kernel.terminated_at is None

    async def test_mark_sessions_terminating_nonexistent_session(
        self,
        schedule_repository: ScheduleRepository,
    ):
        """Test marking non-existent sessions for termination"""
        # Try to mark non-existent sessions
        fake_session_ids = [str(uuid.uuid4()) for _ in range(3)]

        result = await schedule_repository.mark_sessions_terminating(
            fake_session_ids,
            reason="TEST_NONEXISTENT",
        )

        # All should be in skipped category (not found)
        assert len(result.skipped_sessions) == 3
        assert result.processed_count() == 0
        assert result.has_processed() is False

    async def test_get_terminating_sessions_empty(
        self,
        schedule_repository: ScheduleRepository,
    ):
        """Test fetching terminating sessions when none exist"""
        # Clean database state - no terminating sessions
        terminating_sessions = await schedule_repository.get_terminating_sessions()

        # Should return empty list
        assert terminating_sessions == []

    async def test_mark_sessions_terminating_pending_to_cancelled(
        self,
        schedule_repository: ScheduleRepository,
        sample_sessions_for_termination: dict[str, Any],
        db_with_cleanup: ExtendedAsyncSAEngine,
    ):
        """Test that PENDING sessions are properly cancelled"""
        sessions = sample_sessions_for_termination["sessions"]
        pending_session = sessions[0]  # PENDING status

        # Mark pending session for termination
        result = await schedule_repository.mark_sessions_terminating(
            [str(pending_session.id)],
            reason="CANCELLED_BY_USER",
        )

        # Should be in cancelled list
        assert len(result.cancelled_sessions) == 1
        assert str(pending_session.id) in result.cancelled_sessions

        # Verify database updates
        async with db_with_cleanup.begin_readonly_session() as db_sess:
            stmt = sa.select(SessionRow).where(SessionRow.id == pending_session.id)
            updated_session = await db_sess.scalar(stmt)
            assert updated_session.status == SessionStatus.CANCELLED
            assert updated_session.status_info == "CANCELLED_BY_USER"
            # Result field is not updated by cancellation process currently

            # Check kernel is also cancelled
            stmt = sa.select(KernelRow).where(KernelRow.session_id == pending_session.id)
            updated_kernel = await db_sess.scalar(stmt)
            assert updated_kernel.status == KernelStatus.CANCELLED
