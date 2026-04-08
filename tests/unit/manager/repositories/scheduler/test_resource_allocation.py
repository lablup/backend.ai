"""
Tests for per-kernel resource allocation during kernel RUNNING transition.

BA-5627: Ensure update_kernel_status_running activates resource_allocations
(sets used + used_at) and increments agent_resources.used atomically
with the kernel status transition to RUNNING.
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
from ai.backend.manager.errors.resource_slot import AgentResourceCapacityExceeded
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.rbac_models import (
    AssociationScopesEntitiesRow,
    EntityFieldRow,
    RoleRow,
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
from ai.backend.manager.sokovan.data import KernelCreationInfo
from ai.backend.testutils.db import with_tables


def _make_creation_info(
    cpu: str = "2",
    mem: str = "4096",
) -> KernelCreationInfo:
    """Build a KernelCreationInfo whose get_resource_allocations() returns the given slots."""
    return KernelCreationInfo(
        container_id="test-container",
        resource_spec={
            "allocations": {
                "cpu": {"cpu": {"0": cpu}},
                "mem": {"mem": {"0": mem}},
            },
        },
        repl_in_port=2001,
        repl_out_port=2002,
        stdin_port=2003,
        stdout_port=2004,
    )


class TestUpdateKernelStatusRunningResourceAllocation:
    """Tests for resource allocation performed by update_kernel_status_running."""

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
                RoleRow,
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

    async def _create_kernel_with_pending_allocations(
        self,
        db: ExtendedAsyncSAEngine,
        *,
        domain_name: str,
        scaling_group_name: str,
        group_id: uuid.UUID,
        user_uuid: uuid.UUID,
        access_key: AccessKey,
        agent_id: str | None,
        kernel_status: KernelStatus = KernelStatus.CREATING,
        cpu_requested: Decimal = Decimal("2"),
        mem_requested: Decimal = Decimal("4096"),
    ) -> tuple[SessionId, KernelId]:
        """Create a session + kernel with pending (unactivated) resource allocations.

        Resource allocations have used=None and used_at=None, simulating the
        state before update_kernel_status_running is called.
        """
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
                    status=SessionStatus.CREATING,
                    status_info="test",
                    cluster_mode=ClusterMode.SINGLE_NODE,
                    requested_slots=ResourceSlot({"cpu": cpu_requested, "mem": mem_requested}),
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
                    status=kernel_status,
                    status_changed=datetime.now(tzutc()),
                    occupied_slots=ResourceSlot(),
                    requested_slots=ResourceSlot({"cpu": cpu_requested, "mem": mem_requested}),
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

            # Pending allocations: used=None, used_at=None
            for slot_name, requested in [
                ("cpu", cpu_requested),
                ("mem", mem_requested),
            ]:
                db_sess.add(
                    ResourceAllocationRow(
                        kernel_id=kernel_id,
                        slot_name=slot_name,
                        requested=requested,
                    )
                )
            await db_sess.flush()

        return session_id, kernel_id

    async def _seed_agent_resources(
        self,
        db: ExtendedAsyncSAEngine,
        agent_id: str,
        cpu_capacity: Decimal = Decimal("10"),
        mem_capacity: Decimal = Decimal("10240"),
        cpu_used: Decimal = Decimal("0"),
        mem_used: Decimal = Decimal("0"),
    ) -> None:
        """Seed agent_resources rows for the given agent."""
        async with db.begin_session() as db_sess:
            for slot_name, capacity, used in [
                ("cpu", cpu_capacity, cpu_used),
                ("mem", mem_capacity, mem_used),
            ]:
                db_sess.add(
                    AgentResourceRow(
                        agent_id=agent_id,
                        slot_name=slot_name,
                        capacity=capacity,
                        used=used,
                    )
                )
            await db_sess.flush()

    async def test_sets_used_and_used_at_on_resource_allocations(
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
        """update_kernel_status_running sets used and used_at on resource_allocations."""
        await self._seed_agent_resources(db_with_cleanup, test_agent_id)
        _, kernel_id = await self._create_kernel_with_pending_allocations(
            db_with_cleanup,
            domain_name=test_domain_name,
            scaling_group_name=test_scaling_group_name,
            group_id=test_group_id,
            user_uuid=test_user_uuid,
            access_key=test_access_key,
            agent_id=test_agent_id,
            cpu_requested=Decimal("2"),
            mem_requested=Decimal("4096"),
        )

        db_source = ScheduleDBSource(db_with_cleanup)
        result = await db_source.update_kernel_status_running(
            kernel_id, "test-started", _make_creation_info(cpu="2", mem="4096")
        )
        assert result is True

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
                assert alloc.used is not None, f"used should be set for {alloc.slot_name}"
                assert alloc.used_at is not None, f"used_at should be set for {alloc.slot_name}"
                assert alloc.used == alloc.requested

    async def test_increments_agent_resources_used(
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
        """update_kernel_status_running increments agent_resources.used."""
        await self._seed_agent_resources(
            db_with_cleanup, test_agent_id, cpu_used=Decimal("1"), mem_used=Decimal("1024")
        )
        _, kernel_id = await self._create_kernel_with_pending_allocations(
            db_with_cleanup,
            domain_name=test_domain_name,
            scaling_group_name=test_scaling_group_name,
            group_id=test_group_id,
            user_uuid=test_user_uuid,
            access_key=test_access_key,
            agent_id=test_agent_id,
            cpu_requested=Decimal("2"),
            mem_requested=Decimal("4096"),
        )

        db_source = ScheduleDBSource(db_with_cleanup)
        await db_source.update_kernel_status_running(
            kernel_id, "test-started", _make_creation_info(cpu="2", mem="4096")
        )

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
            by_slot = {ar.slot_name: ar.used for ar in agent_resources}
            assert by_slot["cpu"] == Decimal("3")  # 1 + 2
            assert by_slot["mem"] == Decimal("5120")  # 1024 + 4096

    async def test_updates_kernel_status_to_running(
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
        """update_kernel_status_running transitions kernel to RUNNING and sets occupied_slots."""
        await self._seed_agent_resources(db_with_cleanup, test_agent_id)
        _, kernel_id = await self._create_kernel_with_pending_allocations(
            db_with_cleanup,
            domain_name=test_domain_name,
            scaling_group_name=test_scaling_group_name,
            group_id=test_group_id,
            user_uuid=test_user_uuid,
            access_key=test_access_key,
            agent_id=test_agent_id,
        )

        db_source = ScheduleDBSource(db_with_cleanup)
        result = await db_source.update_kernel_status_running(
            kernel_id, "test-started", _make_creation_info()
        )
        assert result is True

        async with db_with_cleanup.begin_readonly_session() as db_sess:
            kernel = (
                await db_sess.execute(sa.select(KernelRow).where(KernelRow.id == kernel_id))
            ).scalar_one()
            assert kernel.status == KernelStatus.RUNNING
            assert kernel.container_id == "test-container"
            assert kernel.occupied_slots["cpu"] is not None
            assert kernel.occupied_slots["mem"] is not None

    async def test_is_idempotent_via_double_call(
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
        """Second call returns False (kernel already RUNNING) and does not double-increment."""
        await self._seed_agent_resources(db_with_cleanup, test_agent_id)
        _, kernel_id = await self._create_kernel_with_pending_allocations(
            db_with_cleanup,
            domain_name=test_domain_name,
            scaling_group_name=test_scaling_group_name,
            group_id=test_group_id,
            user_uuid=test_user_uuid,
            access_key=test_access_key,
            agent_id=test_agent_id,
            cpu_requested=Decimal("2"),
            mem_requested=Decimal("4096"),
        )

        db_source = ScheduleDBSource(db_with_cleanup)
        creation_info = _make_creation_info(cpu="2", mem="4096")

        first = await db_source.update_kernel_status_running(kernel_id, "started", creation_info)
        second = await db_source.update_kernel_status_running(kernel_id, "started", creation_info)
        assert first is True
        assert second is False  # kernel is already RUNNING, not in PREPARED/CREATING

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
            by_slot = {ar.slot_name: ar.used for ar in agent_resources}
            assert by_slot["cpu"] == Decimal("2")  # Not 4
            assert by_slot["mem"] == Decimal("4096")  # Not 8192

    async def test_raises_on_capacity_exceeded(
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
        """update_kernel_status_running raises AgentResourceCapacityExceeded on overflow."""
        await self._seed_agent_resources(
            db_with_cleanup,
            test_agent_id,
            cpu_capacity=Decimal("2"),
            mem_capacity=Decimal("4096"),
            cpu_used=Decimal("1"),
        )
        _, kernel_id = await self._create_kernel_with_pending_allocations(
            db_with_cleanup,
            domain_name=test_domain_name,
            scaling_group_name=test_scaling_group_name,
            group_id=test_group_id,
            user_uuid=test_user_uuid,
            access_key=test_access_key,
            agent_id=test_agent_id,
            cpu_requested=Decimal("4"),
            mem_requested=Decimal("1024"),
        )

        db_source = ScheduleDBSource(db_with_cleanup)
        with pytest.raises(AgentResourceCapacityExceeded):
            await db_source.update_kernel_status_running(
                kernel_id, "test-started", _make_creation_info(cpu="4", mem="1024")
            )

    async def test_returns_false_when_kernel_not_in_valid_status(
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
        """update_kernel_status_running returns False if kernel is not PREPARED/CREATING."""
        await self._seed_agent_resources(db_with_cleanup, test_agent_id)
        _, kernel_id = await self._create_kernel_with_pending_allocations(
            db_with_cleanup,
            domain_name=test_domain_name,
            scaling_group_name=test_scaling_group_name,
            group_id=test_group_id,
            user_uuid=test_user_uuid,
            access_key=test_access_key,
            agent_id=test_agent_id,
            kernel_status=KernelStatus.PENDING,  # Not a valid source status
        )

        db_source = ScheduleDBSource(db_with_cleanup)
        result = await db_source.update_kernel_status_running(
            kernel_id, "test-started", _make_creation_info()
        )
        assert result is False

        # Allocations should remain unactivated
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
            for alloc in allocs:
                assert alloc.used is None
                assert alloc.used_at is None

    async def test_handles_no_agent_gracefully(
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
        """update_kernel_status_running succeeds without allocating when agent_id is None."""
        _, kernel_id = await self._create_kernel_with_pending_allocations(
            db_with_cleanup,
            domain_name=test_domain_name,
            scaling_group_name=test_scaling_group_name,
            group_id=test_group_id,
            user_uuid=test_user_uuid,
            access_key=test_access_key,
            agent_id=None,  # No agent assigned
            kernel_status=KernelStatus.CREATING,
        )

        db_source = ScheduleDBSource(db_with_cleanup)
        result = await db_source.update_kernel_status_running(
            kernel_id, "test-started", _make_creation_info()
        )
        assert result is True

        # Kernel should be RUNNING but allocations remain unactivated
        async with db_with_cleanup.begin_readonly_session() as db_sess:
            kernel = (
                await db_sess.execute(sa.select(KernelRow).where(KernelRow.id == kernel_id))
            ).scalar_one()
            assert kernel.status == KernelStatus.RUNNING

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
            for alloc in allocs:
                assert alloc.used is None
                assert alloc.used_at is None
