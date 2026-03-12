"""
Tests for resource deallocation during force-terminate and bulk-terminate.

Regression tests for BA-5026: Ensure resource_allocations.free_at is set and
agent_resources.used is decremented when sessions/kernels are terminated via:
- _mark_sessions_as_force_terminated() (via mark_sessions_terminating(forced=True))
- update_kernels_to_terminated()
- update_kernel_status_terminated() (greatest() guard for negative values)
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
from ai.backend.manager.data.session.types import SessionStatus
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
from ai.backend.manager.models.resource_slot import AgentResourceRow, ResourceAllocationRow
from ai.backend.manager.models.resource_slot.row import ResourceSlotTypeRow
from ai.backend.manager.models.scaling_group import ScalingGroupOpts, ScalingGroupRow
from ai.backend.manager.models.scheduling_history.row import SessionSchedulingHistoryRow
from ai.backend.manager.models.session import SessionDependencyRow, SessionRow
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.scheduler.db_source.db_source import ScheduleDBSource
from ai.backend.testutils.db import with_tables


class TestForceTerminateResourceDeallocation:
    """Test that force-terminate frees resource_allocations and decrements agent_resources."""

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        """Database connection with tables created. TRUNCATE CASCADE handles cleanup."""
        async with with_tables(
            database_connection,
            [
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
                ResourceSlotTypeRow,
                ResourceAllocationRow,
                AgentResourceRow,
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
        domain_name = f"test-domain-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                DomainRow(
                    name=domain_name,
                    total_resource_slots=ResourceSlot({
                        "cpu": Decimal("1000"),
                        "mem": Decimal("1048576"),
                    }),
                )
            )
            await db_sess.flush()
        yield domain_name

    @pytest.fixture
    async def test_scaling_group_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[str, None]:
        sg_name = f"test-sgroup-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                ScalingGroupRow(
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
            )
            await db_sess.flush()
        yield sg_name

    @pytest.fixture
    async def test_resource_policy_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[str, None]:
        policy_name = f"test-policy-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                ProjectResourcePolicyRow(
                    name=policy_name,
                    max_vfolder_count=10,
                    max_quota_scope_size=-1,
                    max_network_count=10,
                )
            )
            await db_sess.flush()
        yield policy_name

    @pytest.fixture
    async def test_user_resource_policy_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[str, None]:
        policy_name = f"test-user-policy-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                UserResourcePolicyRow(
                    name=policy_name,
                    max_vfolder_count=10,
                    max_quota_scope_size=-1,
                    max_session_count_per_model_session=10,
                    max_customized_image_count=3,
                )
            )
            await db_sess.flush()
        yield policy_name

    @pytest.fixture
    async def test_keypair_resource_policy_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[str, None]:
        policy_name = f"test-keypair-policy-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                KeyPairResourcePolicyRow(
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
            )
            await db_sess.flush()
        yield policy_name

    @pytest.fixture
    async def test_user_uuid(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_user_resource_policy_name: str,
    ) -> AsyncGenerator[uuid.UUID, None]:
        user_uuid = uuid.uuid4()
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                UserRow(
                    uuid=user_uuid,
                    email=f"test-user-{uuid.uuid4().hex[:8]}@test.com",
                    username=f"test-user-{uuid.uuid4().hex[:8]}",
                    role=UserRole.USER,
                    status=UserStatus.ACTIVE,
                    domain_name=test_domain_name,
                    resource_policy=test_user_resource_policy_name,
                )
            )
            await db_sess.flush()
        yield user_uuid

    @pytest.fixture
    async def test_access_key(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_user_uuid: uuid.UUID,
        test_keypair_resource_policy_name: str,
    ) -> AsyncGenerator[AccessKey, None]:
        access_key = AccessKey(f"AKIA{uuid.uuid4().hex[:16].upper()}")
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                KeyPairRow(
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
            )
            await db_sess.flush()
        yield access_key

    @pytest.fixture
    async def test_group_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_resource_policy_name: str,
    ) -> AsyncGenerator[uuid.UUID, None]:
        group_id = uuid.uuid4()
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                GroupRow(
                    id=group_id,
                    name=f"test-group-{uuid.uuid4().hex[:8]}",
                    description="Test group",
                    is_active=True,
                    domain_name=test_domain_name,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts={},
                    resource_policy=test_resource_policy_name,
                )
            )
            await db_sess.flush()
        yield group_id

    @pytest.fixture
    async def test_agent_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_scaling_group_name: str,
    ) -> AsyncGenerator[str, None]:
        agent_id = f"test-agent-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                AgentRow(
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
            )
            await db_sess.flush()
        yield agent_id

    @pytest.fixture
    async def resource_slot_types(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[None, None]:
        """Seed resource slot types required by resource_allocations FK."""
        async with db_with_cleanup.begin_session() as db_sess:
            for slot_name, slot_type in [("cpu", "count"), ("mem", "bytes")]:
                db_sess.add(ResourceSlotTypeRow(slot_name=slot_name, slot_type=slot_type))
            await db_sess.flush()
        yield

    async def _create_session_with_kernel_and_resources(
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
        agent_id: str | None,
        cpu_used: Decimal = Decimal("2"),
        mem_used: Decimal = Decimal("4096"),
    ) -> tuple[SessionId, KernelId]:
        """Create a session with kernel, resource allocations, and agent resources."""
        session_id = SessionId(uuid.uuid4())
        kernel_id = KernelId(uuid.uuid4())

        async with db.begin_session() as db_sess:
            db_sess.add(
                SessionRow(
                    id=session_id,
                    name=f"test-session-{uuid.uuid4().hex[:8]}",
                    session_type=SessionTypes.INTERACTIVE,
                    domain_name=domain_name,
                    group_id=group_id,
                    scaling_group_name=scaling_group_name,
                    status=session_status,
                    status_info="test",
                    cluster_mode=ClusterMode.SINGLE_NODE,
                    requested_slots=ResourceSlot({"cpu": cpu_used, "mem": mem_used}),
                    created_at=datetime.now(tzutc()),
                    images=["python:3.8"],
                    vfolder_mounts=[],
                    environ={},
                    result=SessionResult.UNDEFINED,
                )
            )
            await db_sess.flush()

            db_sess.add(
                KernelRow(
                    id=kernel_id,
                    session_id=session_id,
                    agent=agent_id,
                    agent_addr="127.0.0.1:6001" if agent_id else None,
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
                    occupied_slots=ResourceSlot({"cpu": cpu_used, "mem": mem_used}),
                    requested_slots=ResourceSlot({"cpu": cpu_used, "mem": mem_used}),
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
            )
            await db_sess.flush()

            # Create resource allocations (unfree'd)
            db_sess.add(
                ResourceAllocationRow(
                    kernel_id=kernel_id,
                    slot_name="cpu",
                    requested=cpu_used,
                    used=cpu_used,
                )
            )
            db_sess.add(
                ResourceAllocationRow(
                    kernel_id=kernel_id,
                    slot_name="mem",
                    requested=mem_used,
                    used=mem_used,
                )
            )
            await db_sess.flush()

            # Create agent resources if agent exists
            if agent_id:
                for slot_name, capacity, used in [
                    ("cpu", Decimal("10"), cpu_used),
                    ("mem", Decimal("10240"), mem_used),
                ]:
                    # Use INSERT ON CONFLICT to handle multiple kernels on the same agent
                    existing = await db_sess.execute(
                        sa.select(AgentResourceRow).where(
                            AgentResourceRow.agent_id == agent_id,
                            AgentResourceRow.slot_name == slot_name,
                        )
                    )
                    if existing.first() is None:
                        db_sess.add(
                            AgentResourceRow(
                                agent_id=agent_id,
                                slot_name=slot_name,
                                capacity=capacity,
                                used=used,
                            )
                        )
                    else:
                        await db_sess.execute(
                            sa.update(AgentResourceRow)
                            .where(
                                AgentResourceRow.agent_id == agent_id,
                                AgentResourceRow.slot_name == slot_name,
                            )
                            .values(used=AgentResourceRow.used + used)
                        )
                await db_sess.flush()

        return session_id, kernel_id

    async def test_force_terminate_frees_resources(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_scaling_group_name: str,
        test_group_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
        test_access_key: AccessKey,
        test_agent_id: str,
        resource_slot_types: None,
    ) -> None:
        """Force-terminate sets free_at on allocations and decrements agent_resources.used."""
        db_source = ScheduleDBSource(db_with_cleanup)

        session_id, kernel_id = await self._create_session_with_kernel_and_resources(
            db_with_cleanup,
            session_status=SessionStatus.RUNNING,
            kernel_status=KernelStatus.RUNNING,
            domain_name=test_domain_name,
            scaling_group_name=test_scaling_group_name,
            group_id=test_group_id,
            user_uuid=test_user_uuid,
            access_key=test_access_key,
            agent_id=test_agent_id,
            cpu_used=Decimal("2"),
            mem_used=Decimal("4096"),
        )

        result = await db_source.mark_sessions_terminating([session_id], forced=True)
        assert session_id in result.force_terminated_sessions

        # Verify resource_allocations.free_at is set
        async with db_with_cleanup.begin_readonly_session() as db_sess:
            allocs = (
                (
                    await db_sess.execute(
                        sa.select(ResourceAllocationRow).where(
                            ResourceAllocationRow.kernel_id == kernel_id,
                        )
                    )
                )
                .scalars()
                .all()
            )
            assert len(allocs) == 2
            for alloc in allocs:
                assert alloc.free_at is not None, (
                    f"free_at should be set for slot {alloc.slot_name}"
                )

            # Verify agent_resources.used is decremented to 0
            agent_resources = (
                (
                    await db_sess.execute(
                        sa.select(AgentResourceRow).where(
                            AgentResourceRow.agent_id == test_agent_id,
                        )
                    )
                )
                .scalars()
                .all()
            )
            for ar in agent_resources:
                assert ar.used == Decimal("0"), (
                    f"agent_resources.used for {ar.slot_name} should be 0 after deallocation, "
                    f"got {ar.used}"
                )

    async def test_force_terminate_with_null_agent_still_sets_free_at(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_scaling_group_name: str,
        test_group_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
        test_access_key: AccessKey,
        resource_slot_types: None,
    ) -> None:
        """When agent_id is NULL (offline agent), free_at is still set on allocations."""
        db_source = ScheduleDBSource(db_with_cleanup)

        session_id, kernel_id = await self._create_session_with_kernel_and_resources(
            db_with_cleanup,
            session_status=SessionStatus.RUNNING,
            kernel_status=KernelStatus.RUNNING,
            domain_name=test_domain_name,
            scaling_group_name=test_scaling_group_name,
            group_id=test_group_id,
            user_uuid=test_user_uuid,
            access_key=test_access_key,
            agent_id=None,
        )

        result = await db_source.mark_sessions_terminating([session_id], forced=True)
        assert session_id in result.force_terminated_sessions

        async with db_with_cleanup.begin_readonly_session() as db_sess:
            allocs = (
                (
                    await db_sess.execute(
                        sa.select(ResourceAllocationRow).where(
                            ResourceAllocationRow.kernel_id == kernel_id,
                        )
                    )
                )
                .scalars()
                .all()
            )
            assert len(allocs) == 2
            for alloc in allocs:
                assert alloc.free_at is not None, (
                    f"free_at should be set even with NULL agent for slot {alloc.slot_name}"
                )


class TestBulkTerminateResourceDeallocation:
    """Test that update_kernels_to_terminated frees resources."""

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
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
                ResourceSlotTypeRow,
                ResourceAllocationRow,
                AgentResourceRow,
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
        domain_name = f"test-domain-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                DomainRow(
                    name=domain_name,
                    total_resource_slots=ResourceSlot({
                        "cpu": Decimal("1000"),
                        "mem": Decimal("1048576"),
                    }),
                )
            )
            await db_sess.flush()
        yield domain_name

    @pytest.fixture
    async def test_scaling_group_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[str, None]:
        sg_name = f"test-sgroup-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                ScalingGroupRow(
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
            )
            await db_sess.flush()
        yield sg_name

    @pytest.fixture
    async def test_resource_policy_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[str, None]:
        policy_name = f"test-policy-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                ProjectResourcePolicyRow(
                    name=policy_name,
                    max_vfolder_count=10,
                    max_quota_scope_size=-1,
                    max_network_count=10,
                )
            )
            await db_sess.flush()
        yield policy_name

    @pytest.fixture
    async def test_user_resource_policy_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[str, None]:
        policy_name = f"test-user-policy-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                UserResourcePolicyRow(
                    name=policy_name,
                    max_vfolder_count=10,
                    max_quota_scope_size=-1,
                    max_session_count_per_model_session=10,
                    max_customized_image_count=3,
                )
            )
            await db_sess.flush()
        yield policy_name

    @pytest.fixture
    async def test_keypair_resource_policy_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[str, None]:
        policy_name = f"test-keypair-policy-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                KeyPairResourcePolicyRow(
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
            )
            await db_sess.flush()
        yield policy_name

    @pytest.fixture
    async def test_user_uuid(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_user_resource_policy_name: str,
    ) -> AsyncGenerator[uuid.UUID, None]:
        user_uuid = uuid.uuid4()
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                UserRow(
                    uuid=user_uuid,
                    email=f"test-user-{uuid.uuid4().hex[:8]}@test.com",
                    username=f"test-user-{uuid.uuid4().hex[:8]}",
                    role=UserRole.USER,
                    status=UserStatus.ACTIVE,
                    domain_name=test_domain_name,
                    resource_policy=test_user_resource_policy_name,
                )
            )
            await db_sess.flush()
        yield user_uuid

    @pytest.fixture
    async def test_access_key(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_user_uuid: uuid.UUID,
        test_keypair_resource_policy_name: str,
    ) -> AsyncGenerator[AccessKey, None]:
        access_key = AccessKey(f"AKIA{uuid.uuid4().hex[:16].upper()}")
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                KeyPairRow(
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
            )
            await db_sess.flush()
        yield access_key

    @pytest.fixture
    async def test_group_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_resource_policy_name: str,
    ) -> AsyncGenerator[uuid.UUID, None]:
        group_id = uuid.uuid4()
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                GroupRow(
                    id=group_id,
                    name=f"test-group-{uuid.uuid4().hex[:8]}",
                    description="Test group",
                    is_active=True,
                    domain_name=test_domain_name,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts={},
                    resource_policy=test_resource_policy_name,
                )
            )
            await db_sess.flush()
        yield group_id

    @pytest.fixture
    async def test_agent_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_scaling_group_name: str,
    ) -> AsyncGenerator[str, None]:
        agent_id = f"test-agent-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                AgentRow(
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
            )
            await db_sess.flush()
        yield agent_id

    @pytest.fixture
    async def resource_slot_types(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[None, None]:
        async with db_with_cleanup.begin_session() as db_sess:
            for slot_name, slot_type in [("cpu", "count"), ("mem", "bytes")]:
                db_sess.add(ResourceSlotTypeRow(slot_name=slot_name, slot_type=slot_type))
            await db_sess.flush()
        yield

    async def _create_kernel_with_resources(
        self,
        db: ExtendedAsyncSAEngine,
        *,
        kernel_status: KernelStatus,
        domain_name: str,
        scaling_group_name: str,
        group_id: uuid.UUID,
        user_uuid: uuid.UUID,
        access_key: AccessKey,
        agent_id: str,
        cpu_used: Decimal = Decimal("2"),
        mem_used: Decimal = Decimal("4096"),
    ) -> tuple[SessionId, KernelId]:
        """Create a session+kernel with resource allocations and agent resources."""
        session_id = SessionId(uuid.uuid4())
        kernel_id = KernelId(uuid.uuid4())

        async with db.begin_session() as db_sess:
            db_sess.add(
                SessionRow(
                    id=session_id,
                    name=f"test-session-{uuid.uuid4().hex[:8]}",
                    session_type=SessionTypes.INTERACTIVE,
                    domain_name=domain_name,
                    group_id=group_id,
                    scaling_group_name=scaling_group_name,
                    status=SessionStatus.RUNNING,
                    status_info="test",
                    cluster_mode=ClusterMode.SINGLE_NODE,
                    requested_slots=ResourceSlot({"cpu": cpu_used, "mem": mem_used}),
                    created_at=datetime.now(tzutc()),
                    images=["python:3.8"],
                    vfolder_mounts=[],
                    environ={},
                    result=SessionResult.UNDEFINED,
                )
            )
            await db_sess.flush()

            db_sess.add(
                KernelRow(
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
                    occupied_slots=ResourceSlot({"cpu": cpu_used, "mem": mem_used}),
                    requested_slots=ResourceSlot({"cpu": cpu_used, "mem": mem_used}),
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
            )
            await db_sess.flush()

            db_sess.add(
                ResourceAllocationRow(
                    kernel_id=kernel_id,
                    slot_name="cpu",
                    requested=cpu_used,
                    used=cpu_used,
                )
            )
            db_sess.add(
                ResourceAllocationRow(
                    kernel_id=kernel_id,
                    slot_name="mem",
                    requested=mem_used,
                    used=mem_used,
                )
            )
            await db_sess.flush()

            for slot_name, capacity, used in [
                ("cpu", Decimal("10"), cpu_used),
                ("mem", Decimal("10240"), mem_used),
            ]:
                existing = await db_sess.execute(
                    sa.select(AgentResourceRow).where(
                        AgentResourceRow.agent_id == agent_id,
                        AgentResourceRow.slot_name == slot_name,
                    )
                )
                if existing.first() is None:
                    db_sess.add(
                        AgentResourceRow(
                            agent_id=agent_id,
                            slot_name=slot_name,
                            capacity=capacity,
                            used=used,
                        )
                    )
                else:
                    await db_sess.execute(
                        sa.update(AgentResourceRow)
                        .where(
                            AgentResourceRow.agent_id == agent_id,
                            AgentResourceRow.slot_name == slot_name,
                        )
                        .values(used=AgentResourceRow.used + used)
                    )
            await db_sess.flush()

        return session_id, kernel_id

    async def test_bulk_terminate_frees_resources(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_scaling_group_name: str,
        test_group_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
        test_access_key: AccessKey,
        test_agent_id: str,
        resource_slot_types: None,
    ) -> None:
        """update_kernels_to_terminated sets free_at and decrements agent_resources.used."""
        db_source = ScheduleDBSource(db_with_cleanup)

        _, kernel_id = await self._create_kernel_with_resources(
            db_with_cleanup,
            kernel_status=KernelStatus.RUNNING,
            domain_name=test_domain_name,
            scaling_group_name=test_scaling_group_name,
            group_id=test_group_id,
            user_uuid=test_user_uuid,
            access_key=test_access_key,
            agent_id=test_agent_id,
        )

        updated = await db_source.update_kernels_to_terminated([str(kernel_id)], "test-cleanup")
        assert updated == 1

        async with db_with_cleanup.begin_readonly_session() as db_sess:
            allocs = (
                (
                    await db_sess.execute(
                        sa.select(ResourceAllocationRow).where(
                            ResourceAllocationRow.kernel_id == kernel_id,
                        )
                    )
                )
                .scalars()
                .all()
            )
            assert len(allocs) == 2
            for alloc in allocs:
                assert alloc.free_at is not None

            agent_resources = (
                (
                    await db_sess.execute(
                        sa.select(AgentResourceRow).where(
                            AgentResourceRow.agent_id == test_agent_id,
                        )
                    )
                )
                .scalars()
                .all()
            )
            for ar in agent_resources:
                assert ar.used == Decimal("0")


class TestNegativeValueGuard:
    """Test that greatest() guard prevents negative agent_resources.used values."""

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
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
                ResourceSlotTypeRow,
                ResourceAllocationRow,
                AgentResourceRow,
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
        domain_name = f"test-domain-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                DomainRow(
                    name=domain_name,
                    total_resource_slots=ResourceSlot({
                        "cpu": Decimal("1000"),
                        "mem": Decimal("1048576"),
                    }),
                )
            )
            await db_sess.flush()
        yield domain_name

    @pytest.fixture
    async def test_scaling_group_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[str, None]:
        sg_name = f"test-sgroup-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                ScalingGroupRow(
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
            )
            await db_sess.flush()
        yield sg_name

    @pytest.fixture
    async def test_resource_policy_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[str, None]:
        policy_name = f"test-policy-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                ProjectResourcePolicyRow(
                    name=policy_name,
                    max_vfolder_count=10,
                    max_quota_scope_size=-1,
                    max_network_count=10,
                )
            )
            await db_sess.flush()
        yield policy_name

    @pytest.fixture
    async def test_user_resource_policy_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[str, None]:
        policy_name = f"test-user-policy-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                UserResourcePolicyRow(
                    name=policy_name,
                    max_vfolder_count=10,
                    max_quota_scope_size=-1,
                    max_session_count_per_model_session=10,
                    max_customized_image_count=3,
                )
            )
            await db_sess.flush()
        yield policy_name

    @pytest.fixture
    async def test_keypair_resource_policy_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[str, None]:
        policy_name = f"test-keypair-policy-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                KeyPairResourcePolicyRow(
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
            )
            await db_sess.flush()
        yield policy_name

    @pytest.fixture
    async def test_user_uuid(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_user_resource_policy_name: str,
    ) -> AsyncGenerator[uuid.UUID, None]:
        user_uuid = uuid.uuid4()
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                UserRow(
                    uuid=user_uuid,
                    email=f"test-user-{uuid.uuid4().hex[:8]}@test.com",
                    username=f"test-user-{uuid.uuid4().hex[:8]}",
                    role=UserRole.USER,
                    status=UserStatus.ACTIVE,
                    domain_name=test_domain_name,
                    resource_policy=test_user_resource_policy_name,
                )
            )
            await db_sess.flush()
        yield user_uuid

    @pytest.fixture
    async def test_access_key(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_user_uuid: uuid.UUID,
        test_keypair_resource_policy_name: str,
    ) -> AsyncGenerator[AccessKey, None]:
        access_key = AccessKey(f"AKIA{uuid.uuid4().hex[:16].upper()}")
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                KeyPairRow(
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
            )
            await db_sess.flush()
        yield access_key

    @pytest.fixture
    async def test_group_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_resource_policy_name: str,
    ) -> AsyncGenerator[uuid.UUID, None]:
        group_id = uuid.uuid4()
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                GroupRow(
                    id=group_id,
                    name=f"test-group-{uuid.uuid4().hex[:8]}",
                    description="Test group",
                    is_active=True,
                    domain_name=test_domain_name,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts={},
                    resource_policy=test_resource_policy_name,
                )
            )
            await db_sess.flush()
        yield group_id

    @pytest.fixture
    async def test_agent_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_scaling_group_name: str,
    ) -> AsyncGenerator[str, None]:
        agent_id = f"test-agent-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                AgentRow(
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
            )
            await db_sess.flush()
        yield agent_id

    @pytest.fixture
    async def resource_slot_types(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[None, None]:
        async with db_with_cleanup.begin_session() as db_sess:
            for slot_name, slot_type in [("cpu", "count"), ("mem", "bytes")]:
                db_sess.add(ResourceSlotTypeRow(slot_name=slot_name, slot_type=slot_type))
            await db_sess.flush()
        yield

    async def test_double_terminate_does_not_go_negative(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_scaling_group_name: str,
        test_group_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
        test_access_key: AccessKey,
        test_agent_id: str,
        resource_slot_types: None,
    ) -> None:
        """Calling update_kernel_status_terminated twice doesn't produce negative used values."""
        db_source = ScheduleDBSource(db_with_cleanup)
        session_id = SessionId(uuid.uuid4())
        kernel_id = KernelId(uuid.uuid4())
        cpu_used = Decimal("2")
        mem_used = Decimal("4096")

        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                SessionRow(
                    id=session_id,
                    name=f"test-session-{uuid.uuid4().hex[:8]}",
                    session_type=SessionTypes.INTERACTIVE,
                    domain_name=test_domain_name,
                    group_id=test_group_id,
                    scaling_group_name=test_scaling_group_name,
                    status=SessionStatus.RUNNING,
                    status_info="test",
                    cluster_mode=ClusterMode.SINGLE_NODE,
                    requested_slots=ResourceSlot({"cpu": cpu_used, "mem": mem_used}),
                    created_at=datetime.now(tzutc()),
                    images=["python:3.8"],
                    vfolder_mounts=[],
                    environ={},
                    result=SessionResult.UNDEFINED,
                )
            )
            await db_sess.flush()

            db_sess.add(
                KernelRow(
                    id=kernel_id,
                    session_id=session_id,
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
                    occupied_slots=ResourceSlot({"cpu": cpu_used, "mem": mem_used}),
                    requested_slots=ResourceSlot({"cpu": cpu_used, "mem": mem_used}),
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
            await db_sess.flush()

            db_sess.add(
                ResourceAllocationRow(
                    kernel_id=kernel_id,
                    slot_name="cpu",
                    requested=cpu_used,
                    used=cpu_used,
                )
            )
            db_sess.add(
                ResourceAllocationRow(
                    kernel_id=kernel_id,
                    slot_name="mem",
                    requested=mem_used,
                    used=mem_used,
                )
            )
            await db_sess.flush()

            for slot_name, capacity, used in [
                ("cpu", Decimal("10"), cpu_used),
                ("mem", Decimal("10240"), mem_used),
            ]:
                db_sess.add(
                    AgentResourceRow(
                        agent_id=test_agent_id,
                        slot_name=slot_name,
                        capacity=capacity,
                        used=used,
                    )
                )
            await db_sess.flush()

        # First terminate - should free resources normally
        result1 = await db_source.update_kernel_status_terminated(kernel_id, "first-terminate")
        assert result1 is True

        # Second terminate - free_at already set, so no allocations to free;
        # agent_resources.used should remain at 0, not go negative
        result2 = await db_source.update_kernel_status_terminated(kernel_id, "second-terminate")
        assert result2 is True

        async with db_with_cleanup.begin_readonly_session() as db_sess:
            agent_resources = (
                (
                    await db_sess.execute(
                        sa.select(AgentResourceRow).where(
                            AgentResourceRow.agent_id == test_agent_id,
                        )
                    )
                )
                .scalars()
                .all()
            )
            for ar in agent_resources:
                assert ar.used >= Decimal("0"), (
                    f"agent_resources.used for {ar.slot_name} must not be negative, got {ar.used}"
                )
