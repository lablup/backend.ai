"""
Tests for kernel termination functionality in ScheduleDBSource.
Tests the lost agent kernel cleanup methods with real database operations.
"""

import uuid
from collections.abc import AsyncGenerator
from datetime import datetime, timedelta
from decimal import Decimal

import pytest
import sqlalchemy as sa
from dateutil.tz import tzutc

from ai.backend.common.types import (
    AccessKey,
    AgentId,
    ClusterMode,
    DefaultForUnspecified,
    ResourceSlot,
    SecretKey,
    SessionId,
    SessionResult,
    SessionTypes,
)
from ai.backend.manager.data.agent.types import AgentStatus
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.data.user.types import UserRole, UserStatus
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
from ai.backend.manager.repositories.scheduler.db_source.db_source import ScheduleDBSource
from ai.backend.manager.repositories.scheduler.types.session import (
    KernelTerminationResult,
)
from ai.backend.testutils.db import with_tables


class TestKernelTermination:
    """Test cases for kernel termination with lost agents"""

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
                AgentRow,
                SessionRow,
                KernelRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def test_domain_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[str, None]:
        """Create test domain and return domain name"""
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
        """Create test scaling group and return scaling group name"""
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
        """Create test resource policy and return policy name"""
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
        """Create test user resource policy and return policy name"""
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
        """Create test keypair resource policy and return policy name"""
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
        """Create test user and return user UUID"""
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
        """Create test keypair and return access key"""
        access_key = AccessKey(f"AKTEST{uuid.uuid4().hex[:14]}")
        secret_key = SecretKey(f"SK{uuid.uuid4().hex[:38]}")

        async with db_with_cleanup.begin_session() as db_sess:
            keypair = KeyPairRow(
                access_key=access_key,
                secret_key=secret_key,
                user=test_user_uuid,
                user_id=str(test_user_uuid),
                is_active=True,
                is_admin=False,
                resource_policy=test_keypair_resource_policy_name,
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
        """Create test group and return group ID"""
        group_id = uuid.uuid4()

        async with db_with_cleanup.begin_session() as db_sess:
            group = GroupRow(
                id=group_id,
                name=f"test-group-{uuid.uuid4().hex[:8]}",
                domain_name=test_domain_name,
                total_resource_slots=ResourceSlot({
                    "cpu": Decimal("500"),
                    "mem": Decimal("524288"),
                }),
                resource_policy=test_resource_policy_name,
                integration_id=None,
            )
            db_sess.add(group)
            await db_sess.flush()

        yield group_id

    @pytest.fixture
    async def test_agent_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_scaling_group_name: str,
    ) -> AsyncGenerator[AgentId, None]:
        """Create test agent and return agent ID"""
        agent_id = AgentId(f"test-agent-{uuid.uuid4().hex[:8]}")

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

    @pytest.fixture
    async def test_session_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_scaling_group_name: str,
        test_group_id: uuid.UUID,
    ) -> AsyncGenerator[SessionId, None]:
        """Create test session in TERMINATING status and return session ID"""
        session_id = SessionId(uuid.uuid4())

        async with db_with_cleanup.begin_session() as db_sess:
            session = SessionRow(
                id=session_id,
                name=f"test-session-{uuid.uuid4().hex[:8]}",
                session_type=SessionTypes.INTERACTIVE,
                domain_name=test_domain_name,
                group_id=test_group_id,
                scaling_group_name=test_scaling_group_name,
                status=SessionStatus.TERMINATING,
                status_info="test-termination",
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

        yield session_id

    @pytest.fixture
    async def test_terminating_kernel_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_session_id: SessionId,
        test_agent_id: AgentId,
        test_scaling_group_name: str,
        test_domain_name: str,
        test_group_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
        test_access_key: AccessKey,
    ) -> AsyncGenerator[uuid.UUID, None]:
        """Create test kernel in TERMINATING status and return kernel ID"""
        kernel_id = uuid.uuid4()

        async with db_with_cleanup.begin_session() as db_sess:
            kernel = KernelRow(
                id=kernel_id,
                session_id=test_session_id,
                agent=test_agent_id,
                agent_addr="127.0.0.1:6001",
                scaling_group=test_scaling_group_name,
                cluster_idx=0,
                cluster_role="main",
                cluster_hostname=f"kernel-{uuid.uuid4().hex[:8]}",
                image="python:3.8",
                architecture="x86_64",
                registry="docker.io",
                container_id=f"container-{uuid.uuid4().hex[:8]}",
                status=KernelStatus.TERMINATING,
                status_changed=datetime.now(tzutc()),
                occupied_slots=ResourceSlot({"cpu": Decimal("2"), "mem": Decimal("4096")}),
                requested_slots=ResourceSlot({"cpu": Decimal("2"), "mem": Decimal("4096")}),
                domain_name=test_domain_name,
                group_id=test_group_id,
                user_uuid=test_user_uuid,
                access_key=test_access_key,
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

        yield kernel_id

    @pytest.fixture
    async def test_running_kernel_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_session_id: SessionId,
        test_agent_id: AgentId,
        test_scaling_group_name: str,
        test_domain_name: str,
        test_group_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
        test_access_key: AccessKey,
    ) -> AsyncGenerator[uuid.UUID, None]:
        """Create test kernel in RUNNING status and return kernel ID"""
        kernel_id = uuid.uuid4()

        async with db_with_cleanup.begin_session() as db_sess:
            kernel = KernelRow(
                id=kernel_id,
                session_id=test_session_id,
                agent=test_agent_id,
                agent_addr="127.0.0.1:6001",
                scaling_group=test_scaling_group_name,
                cluster_idx=0,
                cluster_role="main",
                cluster_hostname=f"kernel-{uuid.uuid4().hex[:8]}",
                image="python:3.8",
                architecture="x86_64",
                registry="docker.io",
                container_id=f"container-{uuid.uuid4().hex[:8]}",
                status=KernelStatus.RUNNING,
                status_changed=datetime.now(tzutc()),
                occupied_slots=ResourceSlot({"cpu": Decimal("2"), "mem": Decimal("4096")}),
                requested_slots=ResourceSlot({"cpu": Decimal("2"), "mem": Decimal("4096")}),
                domain_name=test_domain_name,
                group_id=test_group_id,
                user_uuid=test_user_uuid,
                access_key=test_access_key,
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

        yield kernel_id

    async def test_get_terminating_kernels_with_lost_agents(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_session_id: SessionId,
        test_scaling_group_name: str,
        test_domain_name: str,
        test_group_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
        test_access_key: AccessKey,
    ):
        """Test fetching kernels with lost agents - comprehensive scenario"""
        # Create multiple agents with different statuses
        agent_lost = AgentId(f"agent-lost-{uuid.uuid4().hex[:8]}")
        agent_terminated = AgentId(f"agent-terminated-{uuid.uuid4().hex[:8]}")
        agent_alive = AgentId(f"agent-alive-{uuid.uuid4().hex[:8]}")

        # Create multiple kernels with different combinations
        kernel_terminating_lost = uuid.uuid4()
        kernel_terminating_terminated = uuid.uuid4()
        kernel_terminating_alive = uuid.uuid4()
        kernel_running_lost = uuid.uuid4()

        async with db_with_cleanup.begin_session() as db_sess:
            # Create agents
            db_sess.add(
                AgentRow(
                    id=agent_lost,
                    status=AgentStatus.LOST,
                    region="local",
                    scaling_group=test_scaling_group_name,
                    available_slots=ResourceSlot({"cpu": Decimal("10"), "mem": Decimal("10240")}),
                    occupied_slots=ResourceSlot(),
                    addr="127.0.0.1:6001",
                    version="1.0.0",
                    architecture="x86_64",
                )
            )
            db_sess.add(
                AgentRow(
                    id=agent_terminated,
                    status=AgentStatus.TERMINATED,
                    region="local",
                    scaling_group=test_scaling_group_name,
                    available_slots=ResourceSlot({"cpu": Decimal("10"), "mem": Decimal("10240")}),
                    occupied_slots=ResourceSlot(),
                    addr="127.0.0.1:6002",
                    version="1.0.0",
                    architecture="x86_64",
                )
            )
            db_sess.add(
                AgentRow(
                    id=agent_alive,
                    status=AgentStatus.ALIVE,
                    region="local",
                    scaling_group=test_scaling_group_name,
                    available_slots=ResourceSlot({"cpu": Decimal("10"), "mem": Decimal("10240")}),
                    occupied_slots=ResourceSlot(),
                    addr="127.0.0.1:6003",
                    version="1.0.0",
                    architecture="x86_64",
                )
            )

            # Create kernels with different combinations
            # TERMINATING + LOST (should be included)
            db_sess.add(
                KernelRow(
                    id=kernel_terminating_lost,
                    session_id=test_session_id,
                    agent=agent_lost,
                    agent_addr="127.0.0.1:6001",
                    scaling_group=test_scaling_group_name,
                    cluster_idx=0,
                    cluster_role="main",
                    cluster_hostname=f"kernel-{uuid.uuid4().hex[:8]}",
                    image="python:3.8",
                    architecture="x86_64",
                    registry="docker.io",
                    container_id=f"container-{uuid.uuid4().hex[:8]}",
                    status=KernelStatus.TERMINATING,
                    status_changed=datetime.now(tzutc()),
                    occupied_slots=ResourceSlot({"cpu": Decimal("2"), "mem": Decimal("4096")}),
                    requested_slots=ResourceSlot({"cpu": Decimal("2"), "mem": Decimal("4096")}),
                    domain_name=test_domain_name,
                    group_id=test_group_id,
                    user_uuid=test_user_uuid,
                    access_key=test_access_key,
                    mounts=[],
                    environ={},
                    vfolder_mounts=[],
                    preopen_ports=[],
                    repl_in_port=2001,
                    repl_out_port=2002,
                    stdin_port=2003,
                    stdout_port=2004,
                )
            )

            # TERMINATING + TERMINATED (should be included)
            db_sess.add(
                KernelRow(
                    id=kernel_terminating_terminated,
                    session_id=test_session_id,
                    agent=agent_terminated,
                    agent_addr="127.0.0.1:6002",
                    scaling_group=test_scaling_group_name,
                    cluster_idx=0,
                    cluster_role="main",
                    cluster_hostname=f"kernel-{uuid.uuid4().hex[:8]}",
                    image="python:3.8",
                    architecture="x86_64",
                    registry="docker.io",
                    container_id=f"container-{uuid.uuid4().hex[:8]}",
                    status=KernelStatus.TERMINATING,
                    status_changed=datetime.now(tzutc()),
                    occupied_slots=ResourceSlot({"cpu": Decimal("2"), "mem": Decimal("4096")}),
                    requested_slots=ResourceSlot({"cpu": Decimal("2"), "mem": Decimal("4096")}),
                    domain_name=test_domain_name,
                    group_id=test_group_id,
                    user_uuid=test_user_uuid,
                    access_key=test_access_key,
                    mounts=[],
                    environ={},
                    vfolder_mounts=[],
                    preopen_ports=[],
                    repl_in_port=2005,
                    repl_out_port=2006,
                    stdin_port=2007,
                    stdout_port=2008,
                )
            )

            # TERMINATING + ALIVE (should NOT be included)
            db_sess.add(
                KernelRow(
                    id=kernel_terminating_alive,
                    session_id=test_session_id,
                    agent=agent_alive,
                    agent_addr="127.0.0.1:6003",
                    scaling_group=test_scaling_group_name,
                    cluster_idx=0,
                    cluster_role="main",
                    cluster_hostname=f"kernel-{uuid.uuid4().hex[:8]}",
                    image="python:3.8",
                    architecture="x86_64",
                    registry="docker.io",
                    container_id=f"container-{uuid.uuid4().hex[:8]}",
                    status=KernelStatus.TERMINATING,
                    status_changed=datetime.now(tzutc()),
                    occupied_slots=ResourceSlot({"cpu": Decimal("2"), "mem": Decimal("4096")}),
                    requested_slots=ResourceSlot({"cpu": Decimal("2"), "mem": Decimal("4096")}),
                    domain_name=test_domain_name,
                    group_id=test_group_id,
                    user_uuid=test_user_uuid,
                    access_key=test_access_key,
                    mounts=[],
                    environ={},
                    vfolder_mounts=[],
                    preopen_ports=[],
                    repl_in_port=2009,
                    repl_out_port=2010,
                    stdin_port=2011,
                    stdout_port=2012,
                )
            )

            # RUNNING + LOST (should NOT be included - not TERMINATING)
            db_sess.add(
                KernelRow(
                    id=kernel_running_lost,
                    session_id=test_session_id,
                    agent=agent_lost,
                    agent_addr="127.0.0.1:6001",
                    scaling_group=test_scaling_group_name,
                    cluster_idx=0,
                    cluster_role="main",
                    cluster_hostname=f"kernel-{uuid.uuid4().hex[:8]}",
                    image="python:3.8",
                    architecture="x86_64",
                    registry="docker.io",
                    container_id=f"container-{uuid.uuid4().hex[:8]}",
                    status=KernelStatus.RUNNING,
                    status_changed=datetime.now(tzutc()),
                    occupied_slots=ResourceSlot({"cpu": Decimal("2"), "mem": Decimal("4096")}),
                    requested_slots=ResourceSlot({"cpu": Decimal("2"), "mem": Decimal("4096")}),
                    domain_name=test_domain_name,
                    group_id=test_group_id,
                    user_uuid=test_user_uuid,
                    access_key=test_access_key,
                    mounts=[],
                    environ={},
                    vfolder_mounts=[],
                    preopen_ports=[],
                    repl_in_port=2013,
                    repl_out_port=2014,
                    stdin_port=2015,
                    stdout_port=2016,
                )
            )

            await db_sess.flush()

        # Execute
        db_source = ScheduleDBSource(db_with_cleanup)
        result = await db_source.get_terminating_kernels_with_lost_agents()

        # Verify - should find exactly 2 kernels (TERMINATING + LOST, TERMINATING + TERMINATED)
        kernel_ids = [k.kernel_id for k in result]
        assert len(result) == 2
        assert str(kernel_terminating_lost) in kernel_ids
        assert str(kernel_terminating_terminated) in kernel_ids

        # Verify these kernels are NOT included
        assert str(kernel_terminating_alive) not in kernel_ids
        assert str(kernel_running_lost) not in kernel_ids

        # Verify kernel data structure for LOST agent
        found_lost = next(k for k in result if k.kernel_id == str(kernel_terminating_lost))
        assert found_lost.agent_id == agent_lost
        assert found_lost.agent_status == str(AgentStatus.LOST)
        assert found_lost.status == KernelStatus.TERMINATING

        # Verify kernel data structure for TERMINATED agent
        found_terminated = next(
            k for k in result if k.kernel_id == str(kernel_terminating_terminated)
        )
        assert found_terminated.agent_id == agent_terminated
        assert found_terminated.agent_status == str(AgentStatus.TERMINATED)
        assert found_terminated.status == KernelStatus.TERMINATING

    async def test_get_terminating_kernels_with_terminated_agents(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_agent_id: AgentId,
        test_terminating_kernel_id: uuid.UUID,
    ):
        """Test fetching kernels with terminated agents"""
        # Update agent status to TERMINATED
        async with db_with_cleanup.begin_session() as db_sess:
            stmt = (
                sa.update(AgentRow)
                .where(AgentRow.id == test_agent_id)
                .values(status=AgentStatus.TERMINATED)
            )
            await db_sess.execute(stmt)
            await db_sess.flush()

        # Execute
        db_source = ScheduleDBSource(db_with_cleanup)
        result = await db_source.get_terminating_kernels_with_lost_agents()

        # Verify - should find kernel with terminated agent
        assert len(result) >= 1
        kernel_ids = [k.kernel_id for k in result]
        assert str(test_terminating_kernel_id) in kernel_ids

    async def test_get_terminating_kernels_with_no_agent(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_terminating_kernel_id: uuid.UUID,
    ):
        """Test fetching kernels without assigned agents"""
        # Remove agent assignment
        async with db_with_cleanup.begin_session() as db_sess:
            stmt = (
                sa.update(KernelRow)
                .where(KernelRow.id == test_terminating_kernel_id)
                .values(agent=None, agent_addr=None)
            )
            await db_sess.execute(stmt)
            await db_sess.flush()

        # Execute
        db_source = ScheduleDBSource(db_with_cleanup)
        result = await db_source.get_terminating_kernels_with_lost_agents()

        # Verify - should find kernel without agent
        assert len(result) >= 1
        kernel_ids = [k.kernel_id for k in result]
        assert str(test_terminating_kernel_id) in kernel_ids

        # Verify kernel data structure
        found_kernel = next(k for k in result if k.kernel_id == str(test_terminating_kernel_id))
        assert found_kernel.agent_id is None
        assert found_kernel.agent_status is None

    async def test_batch_update_kernels_terminated(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_agent_id: AgentId,
        test_terminating_kernel_id: uuid.UUID,
    ):
        """Test batch updating kernels to TERMINATED status"""
        # Create kernel termination results
        kernel_results = [
            KernelTerminationResult(
                kernel_id=str(test_terminating_kernel_id),
                agent_id=test_agent_id,
                occupied_slots=ResourceSlot(),
                success=True,
            ),
        ]

        # Execute
        db_source = ScheduleDBSource(db_with_cleanup)
        await db_source.batch_update_kernels_terminated(kernel_results, reason="test-swept")

        # Verify - kernel should be TERMINATED
        async with db_with_cleanup.begin_readonly_session() as db_sess:
            stmt = sa.select(KernelRow).where(KernelRow.id == test_terminating_kernel_id)
            updated_kernel = await db_sess.scalar(stmt)
            assert updated_kernel.status == KernelStatus.TERMINATED
            assert updated_kernel.status_info == "test-swept"
            assert updated_kernel.terminated_at is not None

    async def test_batch_update_kernels_terminated_empty_list(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ):
        """Test batch update with empty list should not raise error"""
        db_source = ScheduleDBSource(db_with_cleanup)
        # Should not raise any error
        await db_source.batch_update_kernels_terminated([], reason="test-empty")
