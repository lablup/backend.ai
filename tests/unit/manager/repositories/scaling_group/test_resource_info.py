"""Tests for ResourceInfo feature in ScalingGroupDBSource."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from ai.backend.common.types import ResourceSlot
from ai.backend.manager.data.agent.types import AgentStatus
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.errors.resource import ScalingGroupNotFound
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.rbac_models import UserRoleRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.scaling_group import (
    ScalingGroupOpts,
    ScalingGroupRow,
)
from ai.backend.manager.models.session import SessionId, SessionRow
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.scaling_group.db_source import ScalingGroupDBSource
from ai.backend.testutils.db import with_tables


def _create_kernel(
    session_id: SessionId,
    domain_name: str,
    group_id: uuid.UUID,
    user_uuid: uuid.UUID,
    scaling_group: str,
    agent_id: str,
    status: KernelStatus,
    occupied_slots: ResourceSlot,
    cluster_role: str = "main",
    cluster_idx: int = 0,
) -> KernelRow:
    """Create a KernelRow with all required fields for testing."""
    return KernelRow(
        id=uuid.uuid4(),
        session_id=session_id,
        domain_name=domain_name,
        group_id=group_id,
        user_uuid=user_uuid,
        scaling_group=scaling_group,
        agent=agent_id,
        status=status,
        occupied_slots=occupied_slots,
        requested_slots=occupied_slots,  # Same as occupied for tests
        cluster_role=cluster_role,
        cluster_idx=cluster_idx,
        cluster_hostname=f"{cluster_role}.{session_id}",
        image="python:3.11",
        repl_in_port=0,
        repl_out_port=0,
        stdin_port=0,
        stdout_port=0,
        vfolder_mounts=[],
    )


class TestResourceInfo:
    """Tests for get_resource_info method in ScalingGroupDBSource."""

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        """Database connection with required tables."""
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
                SessionRow,
                AgentRow,
                KernelRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def db_source(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> ScalingGroupDBSource:
        """Create ScalingGroupDBSource instance."""
        return ScalingGroupDBSource(db=db_with_cleanup)

    @pytest.fixture
    async def base_scaling_group(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[str, None]:
        """Create a basic scaling group for testing."""
        sgroup_name = f"test-sgroup-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as db_sess:
            sgroup = ScalingGroupRow(
                name=sgroup_name,
                description="Test scaling group",
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
        yield sgroup_name

    @pytest.fixture
    async def scaling_group_with_alive_schedulable_agents(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        base_scaling_group: str,
    ) -> AsyncGenerator[tuple[str, list[ResourceSlot]], None]:
        """Create scaling group with ALIVE, schedulable agents.

        Returns:
            Tuple of (scaling_group_name, list of agent available_slots)
        """
        agent_slots = [
            ResourceSlot({"cpu": Decimal("4"), "mem": Decimal("8589934592")}),  # 8GB
            ResourceSlot({"cpu": Decimal("8"), "mem": Decimal("17179869184")}),  # 16GB
        ]

        async with db_with_cleanup.begin_session() as db_sess:
            for i, slots in enumerate(agent_slots):
                agent = AgentRow(
                    id=f"agent-alive-sched-{i}-{uuid.uuid4().hex[:8]}",
                    status=AgentStatus.ALIVE,
                    scaling_group=base_scaling_group,
                    schedulable=True,
                    available_slots=slots,
                    occupied_slots=ResourceSlot(),
                    addr="tcp://127.0.0.1:600{i}",
                    region="local",
                    first_contact=datetime.now(tz=UTC),
                    lost_at=None,
                    version="1.0.0",
                    architecture="x86_64",
                    compute_plugins={},
                )
                db_sess.add(agent)

        yield base_scaling_group, agent_slots

    @pytest.fixture
    async def scaling_group_with_mixed_agent_statuses(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        base_scaling_group: str,
    ) -> AsyncGenerator[tuple[str, ResourceSlot], None]:
        """Create scaling group with mixed agent statuses.

        Only ALIVE agents should be counted for capacity.

        Returns:
            Tuple of (scaling_group_name, expected_capacity from ALIVE agent only)
        """
        alive_slots = ResourceSlot({"cpu": Decimal("4"), "mem": Decimal("8589934592")})
        lost_slots = ResourceSlot({"cpu": Decimal("8"), "mem": Decimal("17179869184")})
        terminated_slots = ResourceSlot({"cpu": Decimal("2"), "mem": Decimal("4294967296")})

        async with db_with_cleanup.begin_session() as db_sess:
            # ALIVE agent - should be counted
            db_sess.add(
                AgentRow(
                    id=f"agent-alive-{uuid.uuid4().hex[:8]}",
                    status=AgentStatus.ALIVE,
                    scaling_group=base_scaling_group,
                    schedulable=True,
                    available_slots=alive_slots,
                    occupied_slots=ResourceSlot(),
                    addr="tcp://127.0.0.1:6001",
                    region="local",
                    first_contact=datetime.now(tz=UTC),
                    lost_at=None,
                    version="1.0.0",
                    architecture="x86_64",
                    compute_plugins={},
                )
            )

            # LOST agent - should NOT be counted
            db_sess.add(
                AgentRow(
                    id=f"agent-lost-{uuid.uuid4().hex[:8]}",
                    status=AgentStatus.LOST,
                    scaling_group=base_scaling_group,
                    schedulable=True,
                    available_slots=lost_slots,
                    occupied_slots=ResourceSlot(),
                    addr="tcp://127.0.0.1:6002",
                    region="local",
                    first_contact=datetime.now(tz=UTC),
                    lost_at=datetime.now(tz=UTC),
                    version="1.0.0",
                    architecture="x86_64",
                    compute_plugins={},
                )
            )

            # TERMINATED agent - should NOT be counted
            db_sess.add(
                AgentRow(
                    id=f"agent-terminated-{uuid.uuid4().hex[:8]}",
                    status=AgentStatus.TERMINATED,
                    scaling_group=base_scaling_group,
                    schedulable=True,
                    available_slots=terminated_slots,
                    occupied_slots=ResourceSlot(),
                    addr="tcp://127.0.0.1:6003",
                    region="local",
                    first_contact=datetime.now(tz=UTC),
                    lost_at=datetime.now(tz=UTC),
                    version="1.0.0",
                    architecture="x86_64",
                    compute_plugins={},
                )
            )

        yield base_scaling_group, alive_slots

    @pytest.fixture
    async def scaling_group_with_non_schedulable_agents(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        base_scaling_group: str,
    ) -> AsyncGenerator[tuple[str, ResourceSlot], None]:
        """Create scaling group with schedulable and non-schedulable agents.

        Only schedulable agents should be counted for capacity.

        Returns:
            Tuple of (scaling_group_name, expected_capacity from schedulable agent only)
        """
        schedulable_slots = ResourceSlot({"cpu": Decimal("4"), "mem": Decimal("8589934592")})
        non_schedulable_slots = ResourceSlot({"cpu": Decimal("16"), "mem": Decimal("34359738368")})

        async with db_with_cleanup.begin_session() as db_sess:
            # Schedulable agent - should be counted
            db_sess.add(
                AgentRow(
                    id=f"agent-sched-{uuid.uuid4().hex[:8]}",
                    status=AgentStatus.ALIVE,
                    scaling_group=base_scaling_group,
                    schedulable=True,
                    available_slots=schedulable_slots,
                    occupied_slots=ResourceSlot(),
                    addr="tcp://127.0.0.1:6001",
                    region="local",
                    first_contact=datetime.now(tz=UTC),
                    lost_at=None,
                    version="1.0.0",
                    architecture="x86_64",
                    compute_plugins={},
                )
            )

            # Non-schedulable agent - should NOT be counted
            db_sess.add(
                AgentRow(
                    id=f"agent-non-sched-{uuid.uuid4().hex[:8]}",
                    status=AgentStatus.ALIVE,
                    scaling_group=base_scaling_group,
                    schedulable=False,
                    available_slots=non_schedulable_slots,
                    occupied_slots=ResourceSlot(),
                    addr="tcp://127.0.0.1:6002",
                    region="local",
                    first_contact=datetime.now(tz=UTC),
                    lost_at=None,
                    version="1.0.0",
                    architecture="x86_64",
                    compute_plugins={},
                )
            )

        yield base_scaling_group, schedulable_slots

    @pytest.fixture
    async def test_user_domain_group(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[tuple[uuid.UUID, str, uuid.UUID], None]:
        """Create test domain, user, and group for kernel tests.

        Returns:
            Tuple of (user_uuid, domain_name, group_id)
        """
        from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
        from ai.backend.manager.data.user.types import UserStatus
        from ai.backend.manager.models.hasher.types import PasswordInfo

        test_user_uuid = uuid.uuid4()
        test_domain = f"test-domain-{uuid.uuid4().hex[:8]}"
        test_group_id = uuid.uuid4()
        test_resource_policy = f"test-policy-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            # Create domain
            domain = DomainRow(
                name=test_domain,
                description="Test domain",
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
                created_at=datetime.now(tz=UTC),
                domain_name=test_domain,
                resource_policy=test_resource_policy,
            )
            db_sess.add(user)

            # Create group
            group = GroupRow(
                id=test_group_id,
                name=f"test-group-{uuid.uuid4().hex[:8]}",
                description="Test group",
                is_active=True,
                created_at=datetime.now(tz=UTC),
                domain_name=test_domain,
                total_resource_slots={},
                allowed_vfolder_hosts={},
                resource_policy=test_resource_policy,
            )
            db_sess.add(group)

        yield test_user_uuid, test_domain, test_group_id

    @pytest.fixture
    async def scaling_group_with_running_kernels(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        base_scaling_group: str,
        test_user_domain_group: tuple[uuid.UUID, str, uuid.UUID],
    ) -> AsyncGenerator[tuple[str, ResourceSlot, list[ResourceSlot]], None]:
        """Create scaling group with agent and RUNNING/TERMINATING kernels.

        Returns:
            Tuple of (scaling_group_name, agent_capacity, list of kernel occupied_slots)
        """
        user_uuid, domain_name, group_id = test_user_domain_group

        agent_capacity = ResourceSlot({"cpu": Decimal("16"), "mem": Decimal("34359738368")})
        kernel_slots = [
            ResourceSlot({"cpu": Decimal("2"), "mem": Decimal("4294967296")}),
            ResourceSlot({"cpu": Decimal("4"), "mem": Decimal("8589934592")}),
        ]

        async with db_with_cleanup.begin_session() as db_sess:
            # Create agent
            agent_id = f"agent-{uuid.uuid4().hex[:8]}"
            db_sess.add(
                AgentRow(
                    id=agent_id,
                    status=AgentStatus.ALIVE,
                    scaling_group=base_scaling_group,
                    schedulable=True,
                    available_slots=agent_capacity,
                    occupied_slots=ResourceSlot(),
                    addr="tcp://127.0.0.1:6001",
                    region="local",
                    first_contact=datetime.now(tz=UTC),
                    lost_at=None,
                    version="1.0.0",
                    architecture="x86_64",
                    compute_plugins={},
                )
            )
            await db_sess.flush()

            # Create session and kernels
            session_id = SessionId(uuid.uuid4())
            db_sess.add(
                SessionRow(
                    id=session_id,
                    domain_name=domain_name,
                    group_id=group_id,
                    user_uuid=user_uuid,
                    scaling_group_name=base_scaling_group,
                    cluster_size=2,
                    vfolder_mounts={},
                )
            )
            await db_sess.flush()

            # RUNNING kernel
            db_sess.add(
                _create_kernel(
                    session_id=session_id,
                    domain_name=domain_name,
                    group_id=group_id,
                    user_uuid=user_uuid,
                    scaling_group=base_scaling_group,
                    agent_id=agent_id,
                    status=KernelStatus.RUNNING,
                    occupied_slots=kernel_slots[0],
                    cluster_role="main",
                    cluster_idx=0,
                )
            )

            # TERMINATING kernel
            db_sess.add(
                _create_kernel(
                    session_id=session_id,
                    domain_name=domain_name,
                    group_id=group_id,
                    user_uuid=user_uuid,
                    scaling_group=base_scaling_group,
                    agent_id=agent_id,
                    status=KernelStatus.TERMINATING,
                    occupied_slots=kernel_slots[1],
                    cluster_role="sub",
                    cluster_idx=1,
                )
            )

        yield base_scaling_group, agent_capacity, kernel_slots

    @pytest.fixture
    async def scaling_group_with_mixed_kernel_statuses(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        base_scaling_group: str,
        test_user_domain_group: tuple[uuid.UUID, str, uuid.UUID],
    ) -> AsyncGenerator[tuple[str, ResourceSlot, ResourceSlot], None]:
        """Create scaling group with kernels in various statuses.

        Only RUNNING and TERMINATING kernels should be counted for used.

        Returns:
            Tuple of (scaling_group_name, agent_capacity, expected_used from RUNNING/TERMINATING only)
        """
        user_uuid, domain_name, group_id = test_user_domain_group

        agent_capacity = ResourceSlot({"cpu": Decimal("32"), "mem": Decimal("68719476736")})
        running_slots = ResourceSlot({"cpu": Decimal("2"), "mem": Decimal("4294967296")})
        terminating_slots = ResourceSlot({"cpu": Decimal("4"), "mem": Decimal("8589934592")})
        terminated_slots = ResourceSlot({"cpu": Decimal("8"), "mem": Decimal("17179869184")})
        pending_slots = ResourceSlot({"cpu": Decimal("1"), "mem": Decimal("2147483648")})

        async with db_with_cleanup.begin_session() as db_sess:
            # Create agent
            agent_id = f"agent-{uuid.uuid4().hex[:8]}"
            db_sess.add(
                AgentRow(
                    id=agent_id,
                    status=AgentStatus.ALIVE,
                    scaling_group=base_scaling_group,
                    schedulable=True,
                    available_slots=agent_capacity,
                    occupied_slots=ResourceSlot(),
                    addr="tcp://127.0.0.1:6001",
                    region="local",
                    first_contact=datetime.now(tz=UTC),
                    lost_at=None,
                    version="1.0.0",
                    architecture="x86_64",
                    compute_plugins={},
                )
            )
            await db_sess.flush()

            # Create session
            session_id = SessionId(uuid.uuid4())
            db_sess.add(
                SessionRow(
                    id=session_id,
                    domain_name=domain_name,
                    group_id=group_id,
                    user_uuid=user_uuid,
                    scaling_group_name=base_scaling_group,
                    cluster_size=4,
                    vfolder_mounts={},
                )
            )
            await db_sess.flush()

            # RUNNING kernel - should be counted
            db_sess.add(
                _create_kernel(
                    session_id=session_id,
                    domain_name=domain_name,
                    group_id=group_id,
                    user_uuid=user_uuid,
                    scaling_group=base_scaling_group,
                    agent_id=agent_id,
                    status=KernelStatus.RUNNING,
                    occupied_slots=running_slots,
                    cluster_role="main",
                    cluster_idx=0,
                )
            )

            # TERMINATING kernel - should be counted
            db_sess.add(
                _create_kernel(
                    session_id=session_id,
                    domain_name=domain_name,
                    group_id=group_id,
                    user_uuid=user_uuid,
                    scaling_group=base_scaling_group,
                    agent_id=agent_id,
                    status=KernelStatus.TERMINATING,
                    occupied_slots=terminating_slots,
                    cluster_role="sub",
                    cluster_idx=1,
                )
            )

            # TERMINATED kernel - should NOT be counted
            db_sess.add(
                _create_kernel(
                    session_id=session_id,
                    domain_name=domain_name,
                    group_id=group_id,
                    user_uuid=user_uuid,
                    scaling_group=base_scaling_group,
                    agent_id=agent_id,
                    status=KernelStatus.TERMINATED,
                    occupied_slots=terminated_slots,
                    cluster_role="sub",
                    cluster_idx=2,
                )
            )

            # PENDING kernel - should NOT be counted
            db_sess.add(
                _create_kernel(
                    session_id=session_id,
                    domain_name=domain_name,
                    group_id=group_id,
                    user_uuid=user_uuid,
                    scaling_group=base_scaling_group,
                    agent_id=agent_id,
                    status=KernelStatus.PENDING,
                    occupied_slots=pending_slots,
                    cluster_role="sub",
                    cluster_idx=3,
                )
            )

        expected_used = running_slots + terminating_slots
        yield base_scaling_group, agent_capacity, expected_used

    # =========================
    # Test Cases
    # =========================

    async def test_capacity_sums_alive_schedulable_agents(
        self,
        db_source: ScalingGroupDBSource,
        scaling_group_with_alive_schedulable_agents: tuple[str, list[ResourceSlot]],
    ) -> None:
        """Capacity should sum available_slots from ALIVE, schedulable agents."""
        scaling_group, agent_slots = scaling_group_with_alive_schedulable_agents

        result = await db_source.get_resource_info(scaling_group)

        expected_capacity = agent_slots[0] + agent_slots[1]
        assert result.capacity == expected_capacity

    async def test_excludes_not_alive_agents(
        self,
        db_source: ScalingGroupDBSource,
        scaling_group_with_mixed_agent_statuses: tuple[str, ResourceSlot],
    ) -> None:
        """Capacity should only include ALIVE agents, excluding LOST/TERMINATED."""
        scaling_group, expected_capacity = scaling_group_with_mixed_agent_statuses

        result = await db_source.get_resource_info(scaling_group)

        assert result.capacity == expected_capacity

    async def test_excludes_non_schedulable_agents(
        self,
        db_source: ScalingGroupDBSource,
        scaling_group_with_non_schedulable_agents: tuple[str, ResourceSlot],
    ) -> None:
        """Capacity should only include schedulable agents."""
        scaling_group, expected_capacity = scaling_group_with_non_schedulable_agents

        result = await db_source.get_resource_info(scaling_group)

        assert result.capacity == expected_capacity

    async def test_used_sums_occupied_slots_from_running_terminating_kernels(
        self,
        db_source: ScalingGroupDBSource,
        scaling_group_with_running_kernels: tuple[str, ResourceSlot, list[ResourceSlot]],
    ) -> None:
        """Used should sum occupied_slots from RUNNING/TERMINATING kernels."""
        scaling_group, _, kernel_slots = scaling_group_with_running_kernels

        result = await db_source.get_resource_info(scaling_group)

        expected_used = kernel_slots[0] + kernel_slots[1]
        assert result.used == expected_used

    async def test_used_excludes_non_resource_occupied_kernels(
        self,
        db_source: ScalingGroupDBSource,
        scaling_group_with_mixed_kernel_statuses: tuple[str, ResourceSlot, ResourceSlot],
    ) -> None:
        """Used should only count kernels in resource_occupied_statuses (RUNNING, TERMINATING)."""
        scaling_group, _, expected_used = scaling_group_with_mixed_kernel_statuses

        result = await db_source.get_resource_info(scaling_group)

        assert result.used == expected_used

    async def test_free_equals_capacity_minus_used(
        self,
        db_source: ScalingGroupDBSource,
        scaling_group_with_running_kernels: tuple[str, ResourceSlot, list[ResourceSlot]],
    ) -> None:
        """Free should equal capacity minus used."""
        scaling_group, agent_capacity, kernel_slots = scaling_group_with_running_kernels

        result = await db_source.get_resource_info(scaling_group)

        expected_used = kernel_slots[0] + kernel_slots[1]
        expected_free = agent_capacity - expected_used
        assert result.free == expected_free

    async def test_returns_empty_slots_when_no_agents(
        self,
        db_source: ScalingGroupDBSource,
        base_scaling_group: str,
    ) -> None:
        """Should return empty ResourceSlots when no agents exist."""
        result = await db_source.get_resource_info(base_scaling_group)

        assert result.capacity == ResourceSlot()
        assert result.used == ResourceSlot()
        assert result.free == ResourceSlot()

    async def test_raises_error_for_nonexistent_scaling_group(
        self,
        db_source: ScalingGroupDBSource,
    ) -> None:
        """Should raise ScalingGroupNotFound for non-existent scaling group."""
        nonexistent_group = f"nonexistent-{uuid.uuid4().hex[:8]}"

        with pytest.raises(ScalingGroupNotFound):
            await db_source.get_resource_info(nonexistent_group)
