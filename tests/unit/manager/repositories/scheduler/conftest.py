"""Shared fixtures and helpers for scheduler repository (db_source) tests.

These cover the BA-6134 ``agent_resources.reserved`` feature. The fixtures
build the FK-complete set of rows required to exercise ``ScheduleDBSource``
against a real database via ``with_tables``, and the module-level helpers seed
agent capacity, create PENDING sessions with pending ``resource_allocations``,
and assemble ``AllocationBatch`` values.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from datetime import datetime, timedelta
from decimal import Decimal

import pytest
import sqlalchemy as sa
from dateutil.tz import tzutc

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.identifier.domain import DomainID
from ai.backend.common.identifier.resource_group import ResourceGroupID
from ai.backend.common.types import (
    AccessKey,
    AgentId,
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
from ai.backend.manager.data.sokovan import AllocationBatch, KernelCreationInfo
from ai.backend.manager.data.sokovan.allocation import (
    AgentAllocation,
    KernelAllocation,
    SessionAllocation,
)
from ai.backend.manager.data.user.types import UserStatus
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.image import ImageRow
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
from ai.backend.testutils.db import with_tables

# Tables required to satisfy FK constraints for ScheduleDBSource, in dependency order.
_SCHEDULER_ROWS: list[type] = [
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
    ContainerRegistryRow,
    ImageRow,
    SessionRow,
    KernelRow,
    ResourceSlotTypeRow,
    ResourceAllocationRow,
    AgentResourceRow,
    SessionDependencyRow,
    SessionSchedulingHistoryRow,
]

_AGENT_ADDR = "127.0.0.1:6001"


@pytest.fixture
async def db_with_cleanup(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    """Database connection with the scheduler table set created (TRUNCATE CASCADE cleanup)."""
    async with with_tables(database_connection, _SCHEDULER_ROWS):
        yield database_connection


@pytest.fixture
def test_domain_id() -> DomainID:
    return DomainID(uuid.uuid4())


@pytest.fixture
def test_scaling_group_id() -> ResourceGroupID:
    return ResourceGroupID(uuid.uuid4())


@pytest.fixture
async def test_domain_name(
    db_with_cleanup: ExtendedAsyncSAEngine,
    test_domain_id: DomainID,
) -> AsyncGenerator[str, None]:
    domain_name = f"test-domain-{uuid.uuid4().hex[:8]}"
    async with db_with_cleanup.begin_session() as db_sess:
        db_sess.add(
            DomainRow(
                id=test_domain_id,
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
    db_with_cleanup: ExtendedAsyncSAEngine,
    test_scaling_group_id: ResourceGroupID,
) -> AsyncGenerator[str, None]:
    sg_name = f"test-sgroup-{uuid.uuid4().hex[:8]}"
    async with db_with_cleanup.begin_session() as db_sess:
        db_sess.add(
            ScalingGroupRow(
                id=test_scaling_group_id,
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
                max_containers_per_session=4,
                idle_timeout=600,
                max_session_lifetime=0,
                allowed_vfolder_hosts={},
            )
        )
        await db_sess.flush()
    yield policy_name


@pytest.fixture
async def test_user_uuid(
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
                addr=_AGENT_ADDR,
                version="1.0.0",
                architecture="x86_64",
            )
        )
        await db_sess.flush()
    yield agent_id


@pytest.fixture
async def resource_slot_types(
    db_with_cleanup: ExtendedAsyncSAEngine,
) -> AsyncGenerator[None, None]:
    """Seed resource slot types required by the resource_allocations FK."""
    async with db_with_cleanup.begin_session() as db_sess:
        for slot_name, slot_type in [("cpu", "count"), ("mem", "bytes")]:
            db_sess.add(ResourceSlotTypeRow(slot_name=slot_name, slot_type=slot_type))
        await db_sess.flush()
    yield


# --- Module-level helpers (shared across test files) ---


def make_creation_info(cpu: str = "2", mem: str = "4096") -> KernelCreationInfo:
    """Build a KernelCreationInfo whose get_resource_allocations() returns the given slots."""
    return KernelCreationInfo(
        container_id=f"container-{uuid.uuid4().hex[:8]}",
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


async def seed_agent_resources(
    db: ExtendedAsyncSAEngine,
    agent_id: str,
    *,
    cpu_capacity: Decimal,
    mem_capacity: Decimal,
    cpu_used: Decimal = Decimal("0"),
    mem_used: Decimal = Decimal("0"),
    cpu_reserved: Decimal = Decimal("0"),
    mem_reserved: Decimal = Decimal("0"),
) -> None:
    """Seed agent_resources rows (capacity/used/reserved) for cpu and mem slots."""
    async with db.begin_session() as db_sess:
        for slot_name, capacity, used, reserved in [
            ("cpu", cpu_capacity, cpu_used, cpu_reserved),
            ("mem", mem_capacity, mem_used, mem_reserved),
        ]:
            db_sess.add(
                AgentResourceRow(
                    agent_id=agent_id,
                    slot_name=slot_name,
                    capacity=capacity,
                    used=used,
                    reserved=reserved,
                )
            )
        await db_sess.flush()


async def create_pending_session_with_kernels(
    db: ExtendedAsyncSAEngine,
    *,
    domain_id: DomainID,
    domain_name: str,
    resource_group_id: ResourceGroupID,
    scaling_group_name: str,
    group_id: uuid.UUID,
    user_uuid: uuid.UUID,
    access_key: AccessKey,
    agent_assignments: list[tuple[str, Decimal, Decimal]],
) -> tuple[SessionId, list[KernelId]]:
    """Create a PENDING session with one kernel per agent assignment.

    Each entry in ``agent_assignments`` is ``(agent_id, cpu_requested,
    mem_requested)``. Each kernel is created in PENDING status with pending
    ``resource_allocations`` rows (``used``/``used_at``/``free_at`` all NULL).
    Returns the session id and the kernel ids in assignment order.
    """
    session_id = SessionId(uuid.uuid4())
    kernel_ids: list[KernelId] = []

    total_cpu = sum((cpu for _, cpu, _ in agent_assignments), Decimal("0"))
    total_mem = sum((mem for _, _, mem in agent_assignments), Decimal("0"))

    async with db.begin_session() as db_sess:
        db_sess.add(
            SessionRow(
                id=session_id,
                name=f"test-session-{uuid.uuid4().hex[:8]}",
                session_type=SessionTypes.INTERACTIVE,
                domain_id=domain_id,
                domain_name=domain_name,
                group_id=group_id,
                user_uuid=user_uuid,
                access_key=access_key,
                resource_group_id=resource_group_id,
                scaling_group_name=scaling_group_name,
                status=SessionStatus.PENDING,
                status_info="test",
                cluster_mode=ClusterMode.SINGLE_NODE,
                requested_slots=ResourceSlot({"cpu": total_cpu, "mem": total_mem}),
                created_at=datetime.now(tzutc()),
                images=["python:3.8"],
                vfolder_mounts=[],
                environ={},
                result=SessionResult.UNDEFINED,
            )
        )
        await db_sess.flush()

        for idx, (agent_id, cpu_requested, mem_requested) in enumerate(agent_assignments):
            kernel_id = KernelId(uuid.uuid4())
            kernel_ids.append(kernel_id)
            db_sess.add(
                KernelRow(
                    id=kernel_id,
                    session_id=session_id,
                    agent=None,
                    agent_addr=None,
                    scaling_group=scaling_group_name,
                    resource_group_id=resource_group_id,
                    cluster_idx=idx,
                    cluster_role="main" if idx == 0 else "sub",
                    cluster_hostname=f"kernel-{uuid.uuid4().hex[:8]}",
                    image="python:3.8",
                    architecture="x86_64",
                    registry="docker.io",
                    status=KernelStatus.PENDING,
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

            for slot_name, requested in [("cpu", cpu_requested), ("mem", mem_requested)]:
                db_sess.add(
                    ResourceAllocationRow(
                        kernel_id=kernel_id,
                        slot_name=slot_name,
                        requested=requested,
                    )
                )
            await db_sess.flush()

    return session_id, kernel_ids


def make_allocation_batch(
    *,
    session_id: SessionId,
    scaling_group_name: str,
    access_key: AccessKey,
    kernel_assignments: list[tuple[KernelId, str, Decimal, Decimal]],
) -> AllocationBatch:
    """Assemble a single-session AllocationBatch.

    Each entry in ``kernel_assignments`` is ``(kernel_id, agent_id,
    cpu_slot, mem_slot)``. The reservation amount is taken by the db_source
    from the kernel's pending ``resource_allocations`` rows, so the slots given
    here only feed the (unused-by-reservation) agent_allocations metadata.
    """
    kernel_allocations = [
        KernelAllocation(
            kernel_id=kernel_id,
            agent_id=AgentId(agent_id),
            agent_addr=_AGENT_ADDR,
            scaling_group=scaling_group_name,
        )
        for kernel_id, agent_id, _cpu, _mem in kernel_assignments
    ]
    agent_slots: dict[str, list[ResourceSlot]] = {}
    for _kernel_id, agent_id, cpu, mem in kernel_assignments:
        agent_slots.setdefault(agent_id, []).append(ResourceSlot({"cpu": cpu, "mem": mem}))
    agent_allocations = [
        AgentAllocation(agent_id=AgentId(agent_id), allocated_slots=slots)
        for agent_id, slots in agent_slots.items()
    ]
    allocation = SessionAllocation(
        session_id=session_id,
        session_type=SessionTypes.INTERACTIVE,
        cluster_mode=ClusterMode.SINGLE_NODE,
        scaling_group=scaling_group_name,
        kernel_allocations=kernel_allocations,
        agent_allocations=agent_allocations,
        access_key=access_key,
    )
    return AllocationBatch(allocations=[allocation], failures=[])


async def fetch_agent_resources(
    db: ExtendedAsyncSAEngine,
    agent_id: str,
) -> dict[str, AgentResourceRow]:
    """Return agent_resources rows for the agent keyed by slot name."""
    async with db.begin_readonly_session() as db_sess:
        rows = (
            (
                await db_sess.execute(
                    sa.select(AgentResourceRow).where(AgentResourceRow.agent_id == agent_id)
                )
            )
            .scalars()
            .all()
        )
    return {row.slot_name: row for row in rows}
