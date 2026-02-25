"""
Tests for scheduling history recording in enqueue_session() and mark_sessions_terminating().

Regression tests for BA-4694: Ensure scheduling history records are created
for enqueue (initial creation to PENDING) and RUNNING to TERMINATING transitions.
"""

import uuid
from collections.abc import AsyncGenerator
from datetime import datetime, timedelta
from decimal import Decimal

import pytest
import sqlalchemy as sa
from dateutil.tz import tzutc

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.types import (
    AccessKey,
    ClusterMode,
    DefaultForUnspecified,
    KernelId,
    ResourceSlot,
    SecretKey,
    SessionId,
    SessionResult,
    SessionTypes,
)
from ai.backend.manager.data.agent.types import AgentStatus
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.session.types import SchedulingResult, SessionStatus
from ai.backend.manager.data.user.types import UserStatus
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.rbac_models import (
    AssociationScopesEntitiesRow,
    EntityFieldRow,
    UserRoleRow,
)
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.resource_slot import ResourceAllocationRow
from ai.backend.manager.models.scaling_group import ScalingGroupOpts, ScalingGroupRow
from ai.backend.manager.models.scheduling_history.row import SessionSchedulingHistoryRow
from ai.backend.manager.models.session import SessionDependencyRow, SessionRow
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.scheduler.db_source.db_source import ScheduleDBSource
from ai.backend.manager.repositories.scheduler.types.session_creation import (
    KernelEnqueueData,
    SessionEnqueueData,
)
from ai.backend.testutils.db import with_tables


class TestEnqueueSessionSchedulingHistory:
    """Test that enqueue_session() creates scheduling history records."""

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
                ScalingGroupRow,
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                KeyPairResourcePolicyRow,
                UserRoleRow,
                UserRow,
                KeyPairRow,
                GroupRow,
                AssociationScopesEntitiesRow,
                EntityFieldRow,
                AgentRow,
                SessionRow,
                KernelRow,
                ResourceAllocationRow,
                SessionDependencyRow,
                SessionSchedulingHistoryRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def test_domain_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[str, None]:
        """Create test domain and return domain name."""
        domain_name = f"test-domain-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            domain = DomainRow(
                name=domain_name,
                total_resource_slots=ResourceSlot({
                    "cpu": Decimal("1000"),
                    "mem": Decimal("1048576"),
                }),
            )
            db_sess.add(domain)
            await db_sess.flush()

        yield domain_name

    @pytest.fixture
    async def test_scaling_group_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[str, None]:
        """Create test scaling group and return scaling group name."""
        sg_name = f"test-sgroup-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            sg = ScalingGroupRow(
                name=sg_name,
                driver="static",
                scheduler="fifo",
                scheduler_opts=ScalingGroupOpts(
                    allowed_session_types=[],
                    pending_timeout=timedelta(hours=1),
                    config={},
                ),
                driver_opts={},
                is_active=True,
            )
            db_sess.add(sg)
            await db_sess.flush()

        yield sg_name

    @pytest.fixture
    async def test_resource_policy_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[str, None]:
        """Create test resource policy and return policy name."""
        policy_name = f"test-policy-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            project_policy = ProjectResourcePolicyRow(
                name=policy_name,
                max_vfolder_count=10,
                max_quota_scope_size=-1,
                max_network_count=10,
            )
            db_sess.add(project_policy)
            await db_sess.flush()

        yield policy_name

    @pytest.fixture
    async def test_user_resource_policy_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[str, None]:
        """Create test user resource policy and return policy name."""
        policy_name = f"test-user-policy-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            user_policy = UserResourcePolicyRow(
                name=policy_name,
                max_vfolder_count=10,
                max_quota_scope_size=-1,
                max_session_count_per_model_session=10,
                max_customized_image_count=3,
            )
            db_sess.add(user_policy)
            await db_sess.flush()

        yield policy_name

    @pytest.fixture
    async def test_keypair_resource_policy_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[str, None]:
        """Create test keypair resource policy and return policy name."""
        policy_name = f"test-keypair-policy-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            keypair_policy = KeyPairResourcePolicyRow(
                name=policy_name,
                default_for_unspecified=DefaultForUnspecified.LIMITED,
                total_resource_slots=ResourceSlot({
                    "cpu": Decimal("100"),
                    "mem": Decimal("102400"),
                }),
                max_concurrent_sessions=10,
                max_containers_per_session=1,
                idle_timeout=600,
                max_session_lifetime=0,
                allowed_vfolder_hosts={},
            )
            db_sess.add(keypair_policy)
            await db_sess.flush()

        yield policy_name

    @pytest.fixture
    async def test_user_uuid(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_user_resource_policy_name: str,
    ) -> AsyncGenerator[uuid.UUID, None]:
        """Create test user and return user UUID."""
        user_uuid = uuid.uuid4()

        async with db_with_cleanup.begin_session() as db_sess:
            user = UserRow(
                uuid=user_uuid,
                email=f"test-user-{uuid.uuid4().hex[:8]}@test.com",
                username=f"test-user-{uuid.uuid4().hex[:8]}",
                role=UserRole.USER,
                status=UserStatus.ACTIVE,
                domain_name=test_domain_name,
                resource_policy=test_user_resource_policy_name,
            )
            db_sess.add(user)
            await db_sess.flush()

        yield user_uuid

    @pytest.fixture
    async def test_access_key(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_user_uuid: uuid.UUID,
        test_keypair_resource_policy_name: str,
    ) -> AsyncGenerator[AccessKey, None]:
        """Create test keypair and return access key."""
        access_key = AccessKey(f"AKIA{uuid.uuid4().hex[:16].upper()}")

        async with db_with_cleanup.begin_session() as db_sess:
            keypair = KeyPairRow(
                user_id=f"test-user-{uuid.uuid4().hex[:8]}@test.com",
                access_key=access_key,
                secret_key=SecretKey(f"SK{uuid.uuid4().hex}"),
                is_active=True,
                is_admin=False,
                resource_policy=test_keypair_resource_policy_name,
                rate_limit=1000,
                num_queries=0,
                user=test_user_uuid,
            )
            db_sess.add(keypair)
            await db_sess.flush()

        yield access_key

    @pytest.fixture
    async def test_group_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_resource_policy_name: str,
    ) -> AsyncGenerator[uuid.UUID, None]:
        """Create test group and return group ID."""
        group_id = uuid.uuid4()

        async with db_with_cleanup.begin_session() as db_sess:
            group = GroupRow(
                id=group_id,
                name=f"test-group-{uuid.uuid4().hex[:8]}",
                description="Test group",
                is_active=True,
                domain_name=test_domain_name,
                total_resource_slots=ResourceSlot(),
                allowed_vfolder_hosts={},
                resource_policy=test_resource_policy_name,
            )
            db_sess.add(group)
            await db_sess.flush()

        yield group_id

    @pytest.mark.asyncio
    async def test_enqueue_session_creates_scheduling_history(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_scaling_group_name: str,
        test_group_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
        test_access_key: AccessKey,
    ) -> None:
        """Test that enqueue_session() creates a scheduling history record."""
        db_source = ScheduleDBSource(db_with_cleanup)
        now = datetime.now(tzutc())
        session_id = SessionId(uuid.uuid4())
        kernel_id = KernelId(uuid.uuid4())
        creation_id = f"creation-{uuid.uuid4().hex[:8]}"

        session_data = SessionEnqueueData(
            id=session_id,
            creation_id=creation_id,
            name=f"test-session-{uuid.uuid4().hex[:8]}",
            access_key=test_access_key,
            user_uuid=test_user_uuid,
            group_id=test_group_id,
            domain_name=test_domain_name,
            scaling_group_name=test_scaling_group_name,
            session_type=SessionTypes.INTERACTIVE,
            cluster_mode=ClusterMode.SINGLE_NODE.name,
            cluster_size=1,
            priority=0,
            status=SessionStatus.PENDING.name,
            status_history={SessionStatus.PENDING.name: now.isoformat()},
            requested_slots=ResourceSlot({"cpu": Decimal("1"), "mem": Decimal("1024")}),
            occupying_slots=ResourceSlot(),
            vfolder_mounts=[],
            environ={},
            tag=None,
            starts_at=None,
            batch_timeout=None,
            callback_url=None,
            images=["python:3.8"],
            designated_agent_list=None,
            kernels=[
                KernelEnqueueData(
                    id=kernel_id,
                    session_id=session_id,
                    session_creation_id=creation_id,
                    session_name=f"test-session-{uuid.uuid4().hex[:8]}",
                    session_type=SessionTypes.INTERACTIVE,
                    cluster_mode=ClusterMode.SINGLE_NODE.name,
                    cluster_size=1,
                    cluster_role="main",
                    cluster_idx=0,
                    local_rank=0,
                    cluster_hostname=f"kernel-{uuid.uuid4().hex[:8]}",
                    scaling_group=test_scaling_group_name,
                    domain_name=test_domain_name,
                    group_id=test_group_id,
                    user_uuid=test_user_uuid,
                    access_key=test_access_key,
                    image="python:3.8",
                    architecture="x86_64",
                    registry="docker.io",
                    tag=None,
                    starts_at=None,
                    status=KernelStatus.PENDING.name,
                    status_history={KernelStatus.PENDING.name: now.isoformat()},
                    occupied_slots=ResourceSlot(),
                    requested_slots=ResourceSlot({
                        "cpu": Decimal("1"),
                        "mem": Decimal("1024"),
                    }),
                    occupied_shares={},
                    resource_opts={},
                    environ=[],
                    bootstrap_script=None,
                    startup_command=None,
                    internal_data={},
                    callback_url=None,
                    mounts=[],
                    vfolder_mounts=[],
                    preopen_ports=[],
                    use_host_network=False,
                ),
            ],
            dependencies=[],
        )

        result_id = await db_source.enqueue_session(session_data)
        assert result_id == session_id

        # Verify scheduling history record was created
        async with db_with_cleanup.begin_readonly_session() as db_sess:
            history_stmt = sa.select(SessionSchedulingHistoryRow).where(
                SessionSchedulingHistoryRow.session_id == session_id
            )
            history_record = await db_sess.scalar(history_stmt)
            assert history_record is not None
            assert history_record.phase == "enqueue"
            assert history_record.result == str(SchedulingResult.SUCCESS)
            assert history_record.from_status is None
            assert history_record.to_status == str(SessionStatus.PENDING)
            assert history_record.message == "enqueue success"


class TestMarkTerminatingSchedulingHistory:
    """Test that _mark_sessions_as_terminating() creates scheduling history records."""

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
                ScalingGroupRow,
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                KeyPairResourcePolicyRow,
                UserRoleRow,
                UserRow,
                KeyPairRow,
                GroupRow,
                AgentRow,
                SessionRow,
                KernelRow,
                SessionSchedulingHistoryRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def test_domain_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[str, None]:
        """Create test domain and return domain name."""
        domain_name = f"test-domain-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            domain = DomainRow(
                name=domain_name,
                total_resource_slots=ResourceSlot({
                    "cpu": Decimal("1000"),
                    "mem": Decimal("1048576"),
                }),
            )
            db_sess.add(domain)
            await db_sess.flush()

        yield domain_name

    @pytest.fixture
    async def test_scaling_group_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[str, None]:
        """Create test scaling group and return scaling group name."""
        sg_name = f"test-sgroup-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            sg = ScalingGroupRow(
                name=sg_name,
                driver="static",
                scheduler="fifo",
                scheduler_opts=ScalingGroupOpts(
                    allowed_session_types=[],
                    pending_timeout=timedelta(hours=1),
                    config={},
                ),
                driver_opts={},
                is_active=True,
            )
            db_sess.add(sg)
            await db_sess.flush()

        yield sg_name

    @pytest.fixture
    async def test_resource_policy_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[str, None]:
        """Create test resource policy and return policy name."""
        policy_name = f"test-policy-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            project_policy = ProjectResourcePolicyRow(
                name=policy_name,
                max_vfolder_count=10,
                max_quota_scope_size=-1,
                max_network_count=10,
            )
            db_sess.add(project_policy)
            await db_sess.flush()

        yield policy_name

    @pytest.fixture
    async def test_user_resource_policy_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[str, None]:
        """Create test user resource policy and return policy name."""
        policy_name = f"test-user-policy-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            user_policy = UserResourcePolicyRow(
                name=policy_name,
                max_vfolder_count=10,
                max_quota_scope_size=-1,
                max_session_count_per_model_session=10,
                max_customized_image_count=3,
            )
            db_sess.add(user_policy)
            await db_sess.flush()

        yield policy_name

    @pytest.fixture
    async def test_keypair_resource_policy_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[str, None]:
        """Create test keypair resource policy and return policy name."""
        policy_name = f"test-keypair-policy-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            keypair_policy = KeyPairResourcePolicyRow(
                name=policy_name,
                default_for_unspecified=DefaultForUnspecified.LIMITED,
                total_resource_slots=ResourceSlot({
                    "cpu": Decimal("100"),
                    "mem": Decimal("102400"),
                }),
                max_concurrent_sessions=10,
                max_containers_per_session=1,
                idle_timeout=600,
                max_session_lifetime=0,
                allowed_vfolder_hosts={},
            )
            db_sess.add(keypair_policy)
            await db_sess.flush()

        yield policy_name

    @pytest.fixture
    async def test_user_uuid(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_user_resource_policy_name: str,
    ) -> AsyncGenerator[uuid.UUID, None]:
        """Create test user and return user UUID."""
        user_uuid = uuid.uuid4()

        async with db_with_cleanup.begin_session() as db_sess:
            user = UserRow(
                uuid=user_uuid,
                email=f"test-user-{uuid.uuid4().hex[:8]}@test.com",
                username=f"test-user-{uuid.uuid4().hex[:8]}",
                role=UserRole.USER,
                status=UserStatus.ACTIVE,
                domain_name=test_domain_name,
                resource_policy=test_user_resource_policy_name,
            )
            db_sess.add(user)
            await db_sess.flush()

        yield user_uuid

    @pytest.fixture
    async def test_access_key(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_user_uuid: uuid.UUID,
        test_keypair_resource_policy_name: str,
    ) -> AsyncGenerator[AccessKey, None]:
        """Create test keypair and return access key."""
        access_key = AccessKey(f"AKIA{uuid.uuid4().hex[:16].upper()}")

        async with db_with_cleanup.begin_session() as db_sess:
            keypair = KeyPairRow(
                user_id=f"test-user-{uuid.uuid4().hex[:8]}@test.com",
                access_key=access_key,
                secret_key=SecretKey(f"SK{uuid.uuid4().hex}"),
                is_active=True,
                is_admin=False,
                resource_policy=test_keypair_resource_policy_name,
                rate_limit=1000,
                num_queries=0,
                user=test_user_uuid,
            )
            db_sess.add(keypair)
            await db_sess.flush()

        yield access_key

    @pytest.fixture
    async def test_group_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_resource_policy_name: str,
    ) -> AsyncGenerator[uuid.UUID, None]:
        """Create test group and return group ID."""
        group_id = uuid.uuid4()

        async with db_with_cleanup.begin_session() as db_sess:
            group = GroupRow(
                id=group_id,
                name=f"test-group-{uuid.uuid4().hex[:8]}",
                description="Test group",
                is_active=True,
                domain_name=test_domain_name,
                total_resource_slots=ResourceSlot(),
                allowed_vfolder_hosts={},
                resource_policy=test_resource_policy_name,
            )
            db_sess.add(group)
            await db_sess.flush()

        yield group_id

    @pytest.fixture
    async def test_agent_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_scaling_group_name: str,
    ) -> AsyncGenerator[str, None]:
        """Create test agent and return agent ID."""
        agent_id = f"test-agent-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            agent = AgentRow(
                id=agent_id,
                status=AgentStatus.ALIVE,
                region="local",
                scaling_group=test_scaling_group_name,
                available_slots=ResourceSlot({"cpu": Decimal("10"), "mem": Decimal("10240")}),
                occupied_slots=ResourceSlot(),
                addr="127.0.0.1:6001",
                version="1.0.0",
                architecture="x86_64",
            )
            db_sess.add(agent)
            await db_sess.flush()

        yield agent_id

    async def _create_session_with_kernel(
        self,
        db: ExtendedAsyncSAEngine,
        *,
        session_status: SessionStatus,
        kernel_status: KernelStatus,
        domain_name: str,
        scaling_group_name: str,
        group_id: uuid.UUID,
        user_uuid: uuid.UUID,
        access_key: AccessKey,
        agent_id: str,
    ) -> SessionId:
        """Helper to create a session with a kernel in given statuses."""
        session_id = SessionId(uuid.uuid4())
        kernel_id = uuid.uuid4()

        async with db.begin_session() as db_sess:
            session = SessionRow(
                id=session_id,
                name=f"test-session-{uuid.uuid4().hex[:8]}",
                session_type=SessionTypes.INTERACTIVE,
                domain_name=domain_name,
                group_id=group_id,
                scaling_group_name=scaling_group_name,
                status=session_status,
                status_info="test",
                cluster_mode=ClusterMode.SINGLE_NODE,
                requested_slots=ResourceSlot({"cpu": Decimal("2"), "mem": Decimal("4096")}),
                created_at=datetime.now(tzutc()),
                images=["python:3.8"],
                vfolder_mounts=[],
                environ={},
                result=SessionResult.UNDEFINED,
            )
            db_sess.add(session)
            await db_sess.flush()

            kernel = KernelRow(
                id=kernel_id,
                session_id=session_id,
                agent=agent_id,
                agent_addr="127.0.0.1:6001",
                scaling_group=scaling_group_name,
                cluster_idx=0,
                cluster_role="main",
                cluster_hostname=f"kernel-{uuid.uuid4().hex[:8]}",
                image="python:3.8",
                architecture="x86_64",
                registry="docker.io",
                container_id=f"container-{uuid.uuid4().hex[:8]}",
                status=kernel_status,
                status_changed=datetime.now(tzutc()),
                occupied_slots=ResourceSlot({"cpu": Decimal("2"), "mem": Decimal("4096")}),
                requested_slots=ResourceSlot({"cpu": Decimal("2"), "mem": Decimal("4096")}),
                domain_name=domain_name,
                group_id=group_id,
                user_uuid=user_uuid,
                access_key=access_key,
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
            await db_sess.flush()

        return session_id

    @pytest.mark.asyncio
    async def test_mark_sessions_as_terminating_creates_scheduling_history(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_scaling_group_name: str,
        test_group_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
        test_access_key: AccessKey,
        test_agent_id: str,
    ) -> None:
        """Test that mark_sessions_terminating() creates history records for RUNNING sessions."""
        db_source = ScheduleDBSource(db_with_cleanup)

        session_id = await self._create_session_with_kernel(
            db_with_cleanup,
            session_status=SessionStatus.RUNNING,
            kernel_status=KernelStatus.RUNNING,
            domain_name=test_domain_name,
            scaling_group_name=test_scaling_group_name,
            group_id=test_group_id,
            user_uuid=test_user_uuid,
            access_key=test_access_key,
            agent_id=test_agent_id,
        )

        result = await db_source.mark_sessions_terminating([session_id])
        assert session_id in result.terminating_sessions

        # Verify scheduling history record was created
        async with db_with_cleanup.begin_readonly_session() as db_sess:
            history_stmt = sa.select(SessionSchedulingHistoryRow).where(
                SessionSchedulingHistoryRow.session_id == session_id
            )
            history_record = await db_sess.scalar(history_stmt)
            assert history_record is not None
            assert history_record.phase == "mark_terminating"
            assert history_record.result == str(SchedulingResult.SUCCESS)
            assert history_record.from_status == str(SessionStatus.RUNNING)
            assert history_record.to_status == str(SessionStatus.TERMINATING)
            assert history_record.message == "mark_terminating success"

    @pytest.mark.asyncio
    async def test_mark_sessions_as_terminating_captures_correct_from_status(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_scaling_group_name: str,
        test_group_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
        test_access_key: AccessKey,
        test_agent_id: str,
    ) -> None:
        """Test that different from_statuses are correctly captured for each session."""
        db_source = ScheduleDBSource(db_with_cleanup)

        # Create sessions in different terminatable statuses
        running_session_id = await self._create_session_with_kernel(
            db_with_cleanup,
            session_status=SessionStatus.RUNNING,
            kernel_status=KernelStatus.RUNNING,
            domain_name=test_domain_name,
            scaling_group_name=test_scaling_group_name,
            group_id=test_group_id,
            user_uuid=test_user_uuid,
            access_key=test_access_key,
            agent_id=test_agent_id,
        )
        scheduled_session_id = await self._create_session_with_kernel(
            db_with_cleanup,
            session_status=SessionStatus.SCHEDULED,
            kernel_status=KernelStatus.SCHEDULED,
            domain_name=test_domain_name,
            scaling_group_name=test_scaling_group_name,
            group_id=test_group_id,
            user_uuid=test_user_uuid,
            access_key=test_access_key,
            agent_id=test_agent_id,
        )

        result = await db_source.mark_sessions_terminating([
            running_session_id,
            scheduled_session_id,
        ])
        assert running_session_id in result.terminating_sessions
        assert scheduled_session_id in result.terminating_sessions

        # Verify each history record has the correct from_status
        async with db_with_cleanup.begin_readonly_session() as db_sess:
            # Check RUNNING session history
            running_history_stmt = sa.select(SessionSchedulingHistoryRow).where(
                SessionSchedulingHistoryRow.session_id == running_session_id
            )
            running_history = await db_sess.scalar(running_history_stmt)
            assert running_history is not None
            assert running_history.from_status == str(SessionStatus.RUNNING)
            assert running_history.to_status == str(SessionStatus.TERMINATING)

            # Check SCHEDULED session history
            scheduled_history_stmt = sa.select(SessionSchedulingHistoryRow).where(
                SessionSchedulingHistoryRow.session_id == scheduled_session_id
            )
            scheduled_history = await db_sess.scalar(scheduled_history_stmt)
            assert scheduled_history is not None
            assert scheduled_history.from_status == str(SessionStatus.SCHEDULED)
            assert scheduled_history.to_status == str(SessionStatus.TERMINATING)
