from __future__ import annotations

import secrets
from collections.abc import Mapping, Sequence
from datetime import datetime, timedelta
from decimal import Decimal
from pprint import pprint
from typing import Any, Generator
from unittest import mock
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import attrs
import pytest
import pytest_mock
import trafaret as t
from dateutil.parser import parse as dtparse
from dateutil.tz import tzutc

from ai.backend.common.docker import ImageRef
from ai.backend.common.types import (
    AccessKey,
    AgentId,
    AgentSelectionStrategy,
    ClusterMode,
    KernelId,
    ResourceSlot,
    SessionId,
    SessionTypes,
)
from ai.backend.manager.defs import DEFAULT_ROLE
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.scaling_group import ScalingGroupOpts
from ai.backend.manager.models.session import SessionRow, SessionStatus
from ai.backend.manager.registry import AgentRegistry
from ai.backend.manager.scheduler.agent_selector import (
    DispersedAgentSelector,
    RoundRobinAgentSelector,
)
from ai.backend.manager.scheduler.dispatcher import (
    SchedulerDispatcher,
    _list_managed_sessions,
    load_scheduler,
)
from ai.backend.manager.scheduler.drf import DRFScheduler
from ai.backend.manager.scheduler.fifo import FIFOSlotScheduler, LIFOSlotScheduler
from ai.backend.manager.scheduler.predicates import check_reserved_batch_session
from ai.backend.manager.scheduler.types import InMemoryResourceGroupStateStore

ARCH_FOR_TEST = "x86_64"

agent_selection_resource_priority = ["cuda", "rocm", "tpu", "cpu", "mem"]


def test_load_intrinsic() -> None:
    default_sgroup_opts = ScalingGroupOpts()
    assert isinstance(
        load_scheduler("fifo", default_sgroup_opts, {}),
        FIFOSlotScheduler,
    )
    assert isinstance(
        load_scheduler("lifo", default_sgroup_opts, {}),
        LIFOSlotScheduler,
    )
    assert isinstance(
        load_scheduler("drf", default_sgroup_opts, {}),
        DRFScheduler,
    )


def test_scheduler_configs() -> None:
    example_sgroup_opts = ScalingGroupOpts(  # already processed by column trafaret
        allowed_session_types=[SessionTypes.BATCH],
        pending_timeout=timedelta(seconds=86400 * 2),
        agent_selection_strategy=AgentSelectionStrategy.DISPERSED,
        config={
            "extra_config": None,
            "num_retries_to_skip": 5,
        },
    )
    scheduler = load_scheduler("fifo", example_sgroup_opts, example_sgroup_opts.config)
    assert isinstance(scheduler, FIFOSlotScheduler)
    assert scheduler.config == {
        "extra_config": None,
        "num_retries_to_skip": 5,
    }
    with pytest.raises(t.DataError):
        example_sgroup_opts.config["num_retries_to_skip"] = -1  # type: ignore
        scheduler = load_scheduler(
            "fifo",
            example_sgroup_opts,
            example_sgroup_opts.config,
        )


example_group_id = uuid4()

example_total_capacity = ResourceSlot({"cpu": "4.0", "mem": "4096"})
example_sgroup_name1 = "sg01"
example_sgroup_name2 = "sg02"


@pytest.fixture
def example_agents() -> Sequence[AgentRow]:
    return [
        AgentRow(
            id=AgentId("i-001"),
            addr="10.0.1.1:6001",
            architecture=ARCH_FOR_TEST,
            scaling_group=example_sgroup_name1,
            available_slots=ResourceSlot({
                "cpu": Decimal("4.0"),
                "mem": Decimal("4096"),
                "cuda.shares": Decimal("4.0"),
                "rocm.devices": Decimal("2"),
            }),
            occupied_slots=ResourceSlot({
                "cpu": Decimal("0"),
                "mem": Decimal("0"),
                "cuda.shares": Decimal("0"),
                "rocm.devices": Decimal("0"),
            }),
        ),
        AgentRow(
            id=AgentId("i-101"),
            addr="10.0.2.1:6001",
            architecture=ARCH_FOR_TEST,
            scaling_group=example_sgroup_name2,
            available_slots=ResourceSlot({
                "cpu": Decimal("3.0"),
                "mem": Decimal("2560"),
                "cuda.shares": Decimal("1.0"),
                "rocm.devices": Decimal("8"),
            }),
            occupied_slots=ResourceSlot({
                "cpu": Decimal("0"),
                "mem": Decimal("0"),
                "cuda.shares": Decimal("0"),
                "rocm.devices": Decimal("0"),
            }),
        ),
    ]


@pytest.fixture
def example_agents_many() -> Sequence[AgentRow]:
    return [
        AgentRow(
            id=AgentId("i-001"),
            addr="10.0.1.1:6001",
            architecture=ARCH_FOR_TEST,
            scaling_group=example_sgroup_name1,
            available_slots=ResourceSlot({
                "cpu": Decimal("8"),
                "mem": Decimal("4096"),
                "cuda.shares": Decimal("4.0"),
            }),
            occupied_slots=ResourceSlot({
                "cpu": Decimal("0"),
                "mem": Decimal("0"),
                "cuda.shares": Decimal("0"),
            }),
        ),
        AgentRow(
            id=AgentId("i-002"),
            addr="10.0.2.1:6001",
            architecture=ARCH_FOR_TEST,
            scaling_group=example_sgroup_name2,
            available_slots=ResourceSlot({
                "cpu": Decimal("4"),
                "mem": Decimal("2048"),
                "cuda.shares": Decimal("1.0"),
            }),
            occupied_slots=ResourceSlot({
                "cpu": Decimal("0"),
                "mem": Decimal("0"),
                "cuda.shares": Decimal("0"),
            }),
        ),
        AgentRow(
            id=AgentId("i-003"),
            addr="10.0.3.1:6001",
            architecture=ARCH_FOR_TEST,
            scaling_group=example_sgroup_name2,
            available_slots=ResourceSlot({
                "cpu": Decimal("2"),
                "mem": Decimal("1024"),
                "cuda.shares": Decimal("1.0"),
            }),
            occupied_slots=ResourceSlot({
                "cpu": Decimal("0"),
                "mem": Decimal("0"),
                "cuda.shares": Decimal("0"),
            }),
        ),
        AgentRow(
            id=AgentId("i-004"),
            addr="10.0.4.1:6001",
            architecture=ARCH_FOR_TEST,
            scaling_group=example_sgroup_name2,
            available_slots=ResourceSlot({
                "cpu": Decimal("1"),
                "mem": Decimal("512"),
                "cuda.shares": Decimal("0.5"),
            }),
            occupied_slots=ResourceSlot({
                "cpu": Decimal("0"),
                "mem": Decimal("0"),
                "cuda.shares": Decimal("0"),
            }),
        ),
    ]


@pytest.fixture
def example_agents_multi_homogeneous(
    request: pytest.FixtureRequest,
) -> Generator[Sequence[AgentRow], None, None]:
    repeat = request.param.get("repeat", 10)

    yield [
        AgentRow(
            id=AgentId(f"i-{idx:03d}"),
            addr=f"10.0.1.{idx}:6001",
            architecture=ARCH_FOR_TEST,
            scaling_group=example_sgroup_name1,
            available_slots=ResourceSlot({
                "cpu": Decimal("4.0"),
                "mem": Decimal("4096"),
                "cuda.shares": Decimal("4.0"),
                "rocm.devices": Decimal("2"),
            }),
            occupied_slots=ResourceSlot({
                "cpu": Decimal("0"),
                "mem": Decimal("0"),
                "cuda.shares": Decimal("0"),
                "rocm.devices": Decimal("0"),
            }),
        )
        for idx in range(repeat)
    ]


@pytest.fixture
def example_mixed_agents() -> Sequence[AgentRow]:
    return [
        AgentRow(
            id=AgentId("i-gpu"),
            addr="10.0.1.1:6001",
            architecture=ARCH_FOR_TEST,
            scaling_group=example_sgroup_name1,
            available_slots=ResourceSlot({
                "cpu": Decimal("4.0"),
                "mem": Decimal("4096"),
                "cuda.shares": Decimal("4.0"),
            }),
            occupied_slots=ResourceSlot({
                "cpu": Decimal("0"),
                "mem": Decimal("0"),
                "cuda.shares": Decimal("0"),
            }),
        ),
        AgentRow(
            id=AgentId("i-cpu"),
            addr="10.0.2.1:6001",
            architecture=ARCH_FOR_TEST,
            scaling_group=example_sgroup_name2,
            available_slots=ResourceSlot({
                "cpu": Decimal("3.0"),
                "mem": Decimal("2560"),
                "cuda.shares": Decimal("0"),
            }),
            occupied_slots=ResourceSlot({
                "cpu": Decimal("0"),
                "mem": Decimal("0"),
                "cuda.shares": Decimal("0"),
            }),
        ),
    ]


@pytest.fixture
def example_agents_first_one_assigned() -> Sequence[AgentRow]:
    return [
        AgentRow(
            id=AgentId("i-001"),
            addr="10.0.1.1:6001",
            architecture=ARCH_FOR_TEST,
            scaling_group=example_sgroup_name1,
            available_slots=ResourceSlot({
                "cpu": Decimal("2.0"),
                "mem": Decimal("2048"),
                "cuda.shares": Decimal("2.0"),
                "rocm.devices": Decimal("1"),
            }),
            occupied_slots=ResourceSlot({
                "cpu": Decimal("2.0"),
                "mem": Decimal("2048"),
                "cuda.shares": Decimal("2.0"),
                "rocm.devices": Decimal("1"),
            }),
        ),
        AgentRow(
            id=AgentId("i-101"),
            addr="10.0.2.1:6001",
            architecture=ARCH_FOR_TEST,
            scaling_group=example_sgroup_name2,
            available_slots=ResourceSlot({
                "cpu": Decimal("3.0"),
                "mem": Decimal("2560"),
                "cuda.shares": Decimal("1.0"),
                "rocm.devices": Decimal("8"),
            }),
            occupied_slots=ResourceSlot({
                "cpu": Decimal("0"),
                "mem": Decimal("0"),
                "cuda.shares": Decimal("0"),
                "rocm.devices": Decimal("0"),
            }),
        ),
    ]


@pytest.fixture
def example_agents_no_valid() -> Sequence[AgentRow]:
    return [
        AgentRow(
            id=AgentId("i-001"),
            addr="10.0.1.1:6001",
            architecture=ARCH_FOR_TEST,
            scaling_group=example_sgroup_name1,
            available_slots=ResourceSlot({
                "cpu": Decimal("0"),
                "mem": Decimal("0"),
                "cuda.shares": Decimal("0"),
                "rocm.devices": Decimal("0"),
            }),
            occupied_slots=ResourceSlot({
                "cpu": Decimal("4.0"),
                "mem": Decimal("4096"),
                "cuda.shares": Decimal("4.0"),
                "rocm.devices": Decimal("2"),
            }),
        ),
        AgentRow(
            id=AgentId("i-101"),
            addr="10.0.2.1:6001",
            architecture=ARCH_FOR_TEST,
            scaling_group=example_sgroup_name2,
            available_slots=ResourceSlot({
                "cpu": Decimal("0"),
                "mem": Decimal("0"),
                "cuda.shares": Decimal("0"),
                "rocm.devices": Decimal("0"),
            }),
            occupied_slots=ResourceSlot({
                "cpu": Decimal("3.0"),
                "mem": Decimal("2560"),
                "cuda.shares": Decimal("1.0"),
                "rocm.devices": Decimal("8"),
            }),
        ),
    ]


@attrs.define(auto_attribs=True, slots=True)
class SessionKernelIdPair:
    session_id: SessionId
    kernel_ids: Sequence[KernelId]


cancelled_session_ids = [
    SessionId(UUID("251907d9-1290-4126-bc6c-000000000999")),
]

pending_session_kernel_ids = [
    SessionKernelIdPair(
        session_id=SessionId(UUID("251907d9-1290-4126-bc6c-000000000100")),
        kernel_ids=[KernelId(UUID("251907d9-1290-4126-bc6c-000000000100"))],
    ),
    SessionKernelIdPair(
        session_id=SessionId(UUID("251907d9-1290-4126-bc6c-000000000200")),
        kernel_ids=[KernelId(UUID("251907d9-1290-4126-bc6c-000000000200"))],
    ),
    SessionKernelIdPair(
        # single-node mode multi-container session
        session_id=SessionId(UUID("251907d9-1290-4126-bc6c-000000000300")),
        kernel_ids=[
            KernelId(UUID("251907d9-1290-4126-bc6c-000000000300")),
            KernelId(UUID("251907d9-1290-4126-bc6c-000000000301")),
            KernelId(UUID("251907d9-1290-4126-bc6c-000000000302")),
        ],
    ),
    SessionKernelIdPair(
        session_id=SessionId(UUID("251907d9-1290-4126-bc6c-000000000400")),
        kernel_ids=[KernelId(UUID("251907d9-1290-4126-bc6c-000000000400"))],
    ),
]

existing_session_kernel_ids = [
    SessionKernelIdPair(
        session_id=SessionId(UUID("251907d9-1290-4126-bc6c-100000000100")),
        kernel_ids=[
            KernelId(UUID("251907d9-1290-4126-bc6c-100000000100")),
            KernelId(UUID("251907d9-1290-4126-bc6c-100000000101")),
        ],
    ),
    SessionKernelIdPair(
        session_id=SessionId(UUID("251907d9-1290-4126-bc6c-100000000200")),
        kernel_ids=[KernelId(UUID("251907d9-1290-4126-bc6c-100000000200"))],
    ),
    SessionKernelIdPair(
        # single-node mode multi-container session
        session_id=SessionId(UUID("251907d9-1290-4126-bc6c-100000000300")),
        kernel_ids=[KernelId(UUID("251907d9-1290-4126-bc6c-100000000300"))],
    ),
]

common_image_ref = ImageRef("lablup/python:3.6-ubunt18.04", ["*"], architecture=ARCH_FOR_TEST)
common_image = ImageRow(
    name=common_image_ref.canonical,
    image=common_image_ref.name,
    tag=common_image_ref.tag,
    registry=common_image_ref.registry,
    architecture=ARCH_FOR_TEST,
)

_common_dummy_for_pending_session: Mapping[str, Any] = dict(
    domain_name="default",
    group_id=example_group_id,
    vfolder_mounts=[],
    environ={},
    bootstrap_script=None,
    startup_command=None,
    use_host_network=False,
)

_common_dummy_for_existing_session: Mapping[str, Any] = dict(
    domain_name="default",
    group_id=example_group_id,
)


@pytest.fixture
def example_homogeneous_pending_sessions(
    request: pytest.FixtureRequest,
) -> Generator[Sequence[SessionRow], None, None]:
    repeat = request.param.get("repeat", 10)
    yield [
        SessionRow(
            kernels=[
                KernelRow(
                    id=pending_session_kernel_ids[2].kernel_ids[0],
                    session_id=pending_session_kernel_ids[2].session_id,
                    access_key="dummy-access-key",
                    agent=None,
                    agent_addr=None,
                    cluster_role=DEFAULT_ROLE,
                    cluster_idx=1,
                    local_rank=0,
                    cluster_hostname=f"{DEFAULT_ROLE}0",
                    architecture=common_image_ref.architecture,
                    registry=common_image_ref.registry,
                    image=common_image_ref.name,
                    requested_slots=ResourceSlot({
                        "cpu": Decimal("2.0"),
                        "mem": Decimal("1024"),
                    }),
                    bootstrap_script=None,
                    startup_command=None,
                    created_at=dtparse("2021-12-01T23:59:59+00:00"),
                ),
            ],
            access_key=AccessKey("user01"),
            id=UUID(f"251907d9-1290-4126-bc6c-{idx:012x}"),
            creation_id=f"{idx:012x}",
            name=f"session-{idx}",
            session_type=SessionTypes.BATCH,
            status=SessionStatus.PENDING,
            cluster_mode="single-node",
            cluster_size=1,
            scaling_group_name=example_sgroup_name1,
            requested_slots=ResourceSlot({
                "cpu": Decimal("2.0"),
                "mem": Decimal("1024"),
            }),
            target_sgroup_names=[],
            **_common_dummy_for_pending_session,
            created_at=dtparse("2021-12-28T23:59:59+00:00"),
        )
        for idx in range(repeat)
    ]


@pytest.fixture
def example_cancelled_sessions() -> Sequence[SessionRow]:
    return [
        SessionRow(
            access_key=AccessKey("user01"),
            id=cancelled_session_ids[0],
            creation_id="aaa100",
            name="ecs01",
            session_type=SessionTypes.BATCH,
            status=SessionStatus.PENDING,
            cluster_mode="single-node",
            cluster_size=1,
            scaling_group_name=example_sgroup_name1,
            requested_slots=ResourceSlot({
                "cpu": Decimal("2.0"),
                "mem": Decimal("1024"),
                "cuda.shares": Decimal("0"),
                "rocm.devices": Decimal("1"),
            }),
            target_sgroup_names=[],
            **_common_dummy_for_pending_session,
            created_at=dtparse("2021-12-28T23:59:59+00:00"),
        ),
    ]


def create_pending_session(
    session_id: SessionId, kernel_id: KernelId, requested_slots: ResourceSlot
) -> SessionRow:
    """Create a simple single-kernel pending session."""
    return SessionRow(
        kernels=[
            KernelRow(
                id=session_id,
                session_id=kernel_id,
                access_key="dummy-access-key",
                agent=None,
                agent_addr=None,
                cluster_role=DEFAULT_ROLE,
                cluster_idx=1,
                local_rank=0,
                cluster_hostname=f"{DEFAULT_ROLE}0",
                architecture=common_image_ref.architecture,
                registry=common_image_ref.registry,
                image=common_image_ref.name,
                requested_slots=ResourceSlot({
                    "cpu": Decimal("2.0"),
                    "mem": Decimal("1024"),
                    "cuda.shares": Decimal("0"),
                    "rocm.devices": Decimal("1"),
                }),
                bootstrap_script=None,
                startup_command=None,
                created_at=dtparse("2021-12-28T23:59:59+00:00"),
            ),
        ],
        access_key=AccessKey("user01"),
        id=pending_session_kernel_ids[0].session_id,
        creation_id="aaa100",
        name="eps01",
        session_type=SessionTypes.BATCH,
        status=SessionStatus.PENDING,
        cluster_mode="single-node",
        cluster_size=1,
        scaling_group_name=example_sgroup_name1,
        requested_slots=requested_slots,
        target_sgroup_names=[],
        **_common_dummy_for_pending_session,
        created_at=dtparse("2021-12-28T23:59:59+00:00"),
    )


@pytest.fixture
def example_pending_sessions() -> Sequence[SessionRow]:
    # lower indicies are enqueued first.
    return [
        SessionRow(  # rocm
            kernels=[
                KernelRow(
                    id=pending_session_kernel_ids[0].kernel_ids[0],
                    session_id=pending_session_kernel_ids[0].session_id,
                    access_key="dummy-access-key",
                    agent=None,
                    agent_addr=None,
                    cluster_role=DEFAULT_ROLE,
                    cluster_idx=1,
                    local_rank=0,
                    cluster_hostname=f"{DEFAULT_ROLE}0",
                    architecture=common_image_ref.architecture,
                    registry=common_image_ref.registry,
                    image=common_image_ref.name,
                    requested_slots=ResourceSlot({
                        "cpu": Decimal("2.0"),
                        "mem": Decimal("1024"),
                        "cuda.shares": Decimal("0"),
                        "rocm.devices": Decimal("1"),
                    }),
                    bootstrap_script=None,
                    startup_command=None,
                    created_at=dtparse("2021-12-28T23:59:59+00:00"),
                ),
            ],
            access_key=AccessKey("user01"),
            id=pending_session_kernel_ids[0].session_id,
            creation_id="aaa100",
            name="eps01",
            session_type=SessionTypes.BATCH,
            status=SessionStatus.PENDING,
            cluster_mode="single-node",
            cluster_size=1,
            scaling_group_name=example_sgroup_name1,
            requested_slots=ResourceSlot({
                "cpu": Decimal("2.0"),
                "mem": Decimal("1024"),
                "cuda.shares": Decimal("0"),
                "rocm.devices": Decimal("1"),
            }),
            target_sgroup_names=[],
            **_common_dummy_for_pending_session,
            created_at=dtparse("2021-12-28T23:59:59+00:00"),
        ),
        SessionRow(  # cuda
            kernels=[
                KernelRow(
                    id=pending_session_kernel_ids[1].kernel_ids[0],
                    session_id=pending_session_kernel_ids[1].session_id,
                    access_key="dummy-access-key",
                    agent=None,
                    agent_addr=None,
                    cluster_role=DEFAULT_ROLE,
                    cluster_idx=1,
                    local_rank=0,
                    cluster_hostname=f"{DEFAULT_ROLE}0",
                    architecture=common_image_ref.architecture,
                    registry=common_image_ref.registry,
                    image=common_image_ref.name,
                    requested_slots=ResourceSlot({
                        "cpu": Decimal("1.0"),
                        "mem": Decimal("2048"),
                        "cuda.shares": Decimal("0.5"),
                        "rocm.devices": Decimal("0"),
                    }),
                    bootstrap_script=None,
                    startup_command=None,
                    created_at=dtparse("2022-02-01T23:59:59+00:00"),
                ),
            ],
            access_key=AccessKey("user02"),
            id=pending_session_kernel_ids[1].session_id,
            creation_id="aaa101",
            name="eps02",
            session_type=SessionTypes.BATCH,
            status=SessionStatus.PENDING,
            cluster_mode="single-node",
            cluster_size=1,
            scaling_group_name=example_sgroup_name1,
            requested_slots=ResourceSlot({
                "cpu": Decimal("1.0"),
                "mem": Decimal("2048"),
                "cuda.shares": Decimal("0.5"),
                "rocm.devices": Decimal("0"),
            }),
            target_sgroup_names=[],
            **_common_dummy_for_pending_session,
            created_at=dtparse("2022-02-01T23:59:59+00:00"),
        ),
        SessionRow(  # cpu-only
            kernels=[
                KernelRow(
                    id=pending_session_kernel_ids[2].kernel_ids[0],
                    session_id=pending_session_kernel_ids[2].session_id,
                    access_key="dummy-access-key",
                    agent=None,
                    agent_addr=None,
                    cluster_role=DEFAULT_ROLE,
                    cluster_idx=1,
                    local_rank=0,
                    cluster_hostname=f"{DEFAULT_ROLE}0",
                    architecture=common_image_ref.architecture,
                    registry=common_image_ref.registry,
                    image=common_image_ref.name,
                    requested_slots=ResourceSlot({
                        "cpu": Decimal("0.4"),
                        "mem": Decimal("512"),
                        "cuda.shares": Decimal("0"),
                        "rocm.devices": Decimal("0"),
                    }),
                    bootstrap_script=None,
                    startup_command=None,
                    created_at=dtparse("2021-12-01T23:59:59+00:00"),
                ),
                KernelRow(
                    id=pending_session_kernel_ids[2].kernel_ids[1],
                    session_id=pending_session_kernel_ids[2].session_id,
                    access_key="dummy-access-key",
                    agent=None,
                    agent_addr=None,
                    cluster_role="sub",
                    cluster_idx=2,
                    local_rank=1,
                    cluster_hostname="sub1",
                    architecture=common_image_ref.architecture,
                    registry=common_image_ref.registry,
                    image=common_image_ref.name,
                    requested_slots=ResourceSlot({
                        "cpu": Decimal("0.3"),
                        "mem": Decimal("256"),
                        "cuda.shares": Decimal("0"),
                        "rocm.devices": Decimal("0"),
                    }),
                    bootstrap_script=None,
                    startup_command=None,
                    created_at=dtparse("2021-12-01T23:59:59+00:00"),
                ),
                KernelRow(
                    id=pending_session_kernel_ids[2].kernel_ids[2],
                    session_id=pending_session_kernel_ids[2].session_id,
                    access_key="dummy-access-key",
                    agent=None,
                    agent_addr=None,
                    cluster_role="sub",
                    cluster_idx=3,
                    local_rank=2,
                    cluster_hostname="sub2",
                    architecture=common_image_ref.architecture,
                    registry=common_image_ref.registry,
                    image=common_image_ref.name,
                    requested_slots=ResourceSlot({
                        "cpu": Decimal("0.3"),
                        "mem": Decimal("256"),
                        "cuda.shares": Decimal("0"),
                        "rocm.devices": Decimal("0"),
                    }),
                    bootstrap_script=None,
                    startup_command=None,
                    created_at=dtparse("2021-12-01T23:59:59+00:00"),
                ),
            ],
            access_key=AccessKey("user03"),
            status_data={},
            id=pending_session_kernel_ids[2].session_id,
            creation_id="aaa102",
            name="eps03",
            session_type=SessionTypes.BATCH,
            status=SessionStatus.PENDING,
            cluster_mode="single-node",
            cluster_size=3,
            scaling_group_name=example_sgroup_name1,
            requested_slots=ResourceSlot({
                "cpu": Decimal("1.0"),
                "mem": Decimal("1024"),
                "cuda.shares": Decimal("0"),
                "rocm.devices": Decimal("0"),
            }),
            target_sgroup_names=[],
            **_common_dummy_for_pending_session,
            created_at=dtparse("2021-12-01T23:59:59+00:00"),
        ),
    ]


@pytest.fixture
def example_existing_sessions() -> Sequence[SessionRow]:
    return [
        SessionRow(
            kernels=[
                KernelRow(
                    id=existing_session_kernel_ids[0].kernel_ids[0],
                    session_id=existing_session_kernel_ids[0].session_id,
                    access_key="dummy-access-key",
                    agent=None,
                    agent_addr=None,
                    cluster_role=DEFAULT_ROLE,
                    cluster_idx=1,
                    local_rank=0,
                    cluster_hostname=f"{DEFAULT_ROLE}0",
                    architecture=common_image_ref.architecture,
                    registry=common_image_ref.registry,
                    image=common_image_ref.name,
                    requested_slots=ResourceSlot({
                        "cpu": Decimal("1.0"),
                        "mem": Decimal("512"),
                        "cuda.shares": Decimal("0"),
                        "rocm.devices": Decimal("0"),
                    }),
                    bootstrap_script=None,
                    startup_command=None,
                    created_at=dtparse("2022-02-05T00:00:00+00:00"),
                ),
                KernelRow(
                    id=existing_session_kernel_ids[0].kernel_ids[1],
                    session_id=existing_session_kernel_ids[0].session_id,
                    access_key="dummy-access-key",
                    agent=None,
                    agent_addr=None,
                    cluster_role="sub",
                    cluster_idx=2,
                    local_rank=1,
                    cluster_hostname="sub1",
                    architecture=common_image_ref.architecture,
                    registry=common_image_ref.registry,
                    image=common_image_ref.name,
                    requested_slots=ResourceSlot({
                        "cpu": Decimal("2.0"),
                        "mem": Decimal("512"),
                        "cuda.shares": Decimal("0"),
                        "rocm.devices": Decimal("1"),
                    }),
                    bootstrap_script=None,
                    startup_command=None,
                    created_at=dtparse("2022-02-05T00:00:00+00:00"),
                ),
            ],
            access_key=AccessKey("user01"),
            id=existing_session_kernel_ids[0].session_id,
            name="ees01",
            session_type=SessionTypes.BATCH,
            status=SessionStatus.RUNNING,
            cluster_mode="single-node",
            cluster_size=2,
            occupying_slots=ResourceSlot({
                "cpu": Decimal("3.0"),
                "mem": Decimal("1024"),
                "cuda.shares": Decimal("0"),
                "rocm.devices": Decimal("1"),
            }),
            scaling_group_name=example_sgroup_name1,
            **_common_dummy_for_existing_session,
        ),
        SessionRow(
            kernels=[
                KernelRow(
                    id=existing_session_kernel_ids[1].kernel_ids[0],
                    session_id=existing_session_kernel_ids[1].session_id,
                    access_key="dummy-access-key",
                    agent=None,
                    agent_addr=None,
                    cluster_role=DEFAULT_ROLE,
                    cluster_idx=1,
                    local_rank=0,
                    cluster_hostname=f"{DEFAULT_ROLE}0",
                    architecture=common_image_ref.architecture,
                    registry=common_image_ref.registry,
                    image=common_image_ref.name,
                    requested_slots=ResourceSlot({
                        "cpu": Decimal("1.0"),
                        "mem": Decimal("2048"),
                        "cuda.shares": Decimal("0.5"),
                        "rocm.devices": Decimal("0"),
                    }),
                    bootstrap_script=None,
                    startup_command=None,
                    created_at=dtparse("2021-09-03T00:00:00+00:00"),
                ),
            ],
            access_key=AccessKey("user02"),
            id=existing_session_kernel_ids[1].session_id,
            session_type=SessionTypes.BATCH,
            status=SessionStatus.RUNNING,
            name="ees02",
            cluster_mode="single-node",
            cluster_size=1,
            occupying_slots=ResourceSlot({
                "cpu": Decimal("1.0"),
                "mem": Decimal("2048"),
                "cuda.shares": Decimal("0.5"),
                "rocm.devices": Decimal("0"),
            }),
            scaling_group_name=example_sgroup_name1,
            **_common_dummy_for_existing_session,
        ),
        SessionRow(
            kernels=[
                KernelRow(
                    id=existing_session_kernel_ids[2].kernel_ids[0],
                    session_id=existing_session_kernel_ids[2].session_id,
                    access_key="dummy-access-key",
                    agent=None,
                    agent_addr=None,
                    cluster_role=DEFAULT_ROLE,
                    cluster_idx=1,
                    local_rank=0,
                    cluster_hostname=f"{DEFAULT_ROLE}0",
                    architecture=common_image_ref.architecture,
                    registry=common_image_ref.registry,
                    image=common_image_ref.name,
                    requested_slots=ResourceSlot({
                        "cpu": Decimal("4.0"),
                        "mem": Decimal("4096"),
                        "cuda.shares": Decimal("0"),
                        "rocm.devices": Decimal("0"),
                    }),
                    bootstrap_script=None,
                    startup_command=None,
                    created_at=dtparse("2022-01-15T00:00:00+00:00"),
                ),
            ],
            access_key=AccessKey("user03"),
            id=existing_session_kernel_ids[2].session_id,
            session_type=SessionTypes.BATCH,
            status=SessionStatus.RUNNING,
            name="ees03",
            cluster_mode="single-node",
            cluster_size=1,
            occupying_slots=ResourceSlot({
                "cpu": Decimal("4.0"),
                "mem": Decimal("4096"),
                "cuda.shares": Decimal("0"),
                "rocm.devices": Decimal("0"),
            }),
            scaling_group_name=example_sgroup_name1,
            **_common_dummy_for_existing_session,
        ),
    ]


def _find_and_pop_picked_session(pending_sessions, picked_session_id) -> SessionRow:
    for picked_idx, pending_sess in enumerate(pending_sessions):
        if pending_sess.id == picked_session_id:
            break
    else:
        # no matching entry for picked session?
        raise RuntimeError("should not reach here")
    return pending_sessions.pop(picked_idx)


def _update_agent_assignment(
    agents: list[AgentRow],
    picked_agent_id: AgentId,
    occupied_slots: ResourceSlot,
) -> None:
    for ag in agents:
        if ag.id == picked_agent_id:
            ag.occupied_slots += occupied_slots


@pytest.mark.asyncio
async def test_fifo_scheduler(
    example_agents: Sequence[AgentRow],
    example_pending_sessions: Sequence[SessionRow],
    example_existing_sessions: Sequence[SessionRow],
) -> None:
    scheduler = FIFOSlotScheduler(ScalingGroupOpts(), {})
    agstate_cls = DispersedAgentSelector.get_state_cls()
    agselector = DispersedAgentSelector(
        ScalingGroupOpts(),
        {},
        agent_selection_resource_priority,
        state_store=InMemoryResourceGroupStateStore(agstate_cls),
    )
    picked_session_id = scheduler.pick_session(
        sum((ag.available_slots for ag in example_agents), start=ResourceSlot()),
        example_pending_sessions,
        example_existing_sessions,
    )
    assert picked_session_id == example_pending_sessions[0].id
    picked_session = _find_and_pop_picked_session(
        example_pending_sessions,
        picked_session_id,
    )
    agent_id = await agselector.assign_agent_for_session(
        example_agents,
        picked_session,
    )
    assert agent_id == AgentId("i-001")


@pytest.mark.asyncio
async def test_lifo_scheduler(
    example_agents: Sequence[AgentRow],
    example_pending_sessions: Sequence[SessionRow],
    example_existing_sessions: Sequence[SessionRow],
) -> None:
    scheduler = LIFOSlotScheduler(ScalingGroupOpts(), {})
    agstate_cls = DispersedAgentSelector.get_state_cls()
    agselector = DispersedAgentSelector(
        ScalingGroupOpts(),
        {},
        agent_selection_resource_priority,
        state_store=InMemoryResourceGroupStateStore(agstate_cls),
    )
    picked_session_id = scheduler.pick_session(
        sum((ag.available_slots for ag in example_agents), start=ResourceSlot()),
        example_pending_sessions,
        example_existing_sessions,
    )
    assert picked_session_id == example_pending_sessions[2].id
    picked_session = _find_and_pop_picked_session(
        example_pending_sessions,
        picked_session_id,
    )
    agent_id = await agselector.assign_agent_for_session(
        example_agents,
        picked_session,
    )
    assert agent_id == "i-001"


@pytest.mark.asyncio
async def test_fifo_scheduler_favor_cpu_for_requests_without_accelerators(
    example_mixed_agents: Sequence[AgentRow],
    example_pending_sessions: Sequence[SessionRow],
) -> None:
    scheduler = FIFOSlotScheduler(ScalingGroupOpts(), {})
    agstate_cls = DispersedAgentSelector.get_state_cls()
    agselector = DispersedAgentSelector(
        ScalingGroupOpts(),
        {},
        agent_selection_resource_priority,
        state_store=InMemoryResourceGroupStateStore(agstate_cls),
    )
    total_capacity = sum((ag.available_slots for ag in example_mixed_agents), start=ResourceSlot())
    for idx in range(3):
        picked_session_id = scheduler.pick_session(
            total_capacity,
            example_pending_sessions,
            [],
        )
        assert picked_session_id == example_pending_sessions[0].id
        picked_session = _find_and_pop_picked_session(
            example_pending_sessions,
            picked_session_id,
        )
        agent_id = await agselector.assign_agent_for_session(
            example_mixed_agents,
            picked_session,
        )
        if idx == 0:
            # example_mixed_agents do not have any agent with ROCM accelerators.
            assert agent_id is None
        elif idx == 1:
            assert agent_id == AgentId("i-gpu")
        elif idx == 2:
            # It should favor the CPU-only agent if the requested slots
            # do not include accelerators.
            assert agent_id == AgentId("i-cpu")


def gen_pending_for_holb_tests(session_id: str, status_data: Mapping[str, Any]) -> SessionRow:
    return SessionRow(
        id=SessionId(session_id),  # type: ignore
        status_data=status_data,
        name=secrets.token_hex(8),
        access_key=AccessKey("ak1"),
        creation_id=secrets.token_urlsafe(8),
        kernels=[],
        session_type=SessionTypes.INTERACTIVE,
        cluster_mode=ClusterMode.SINGLE_NODE,
        cluster_size=1,
        scaling_group_name=example_sgroup_name1,
        requested_slots=ResourceSlot({"cpu": Decimal(1), "mem": Decimal(1024)}),
        target_sgroup_names=[],
        **_common_dummy_for_pending_session,
        created_at=dtparse("2020-03-21T00:00:00+00:00"),
    )


def test_fifo_scheduler_hol_blocking_avoidance_empty_status_data() -> None:
    """
    Without any status_data, it should just pick the first session.
    """
    scheduler = FIFOSlotScheduler(ScalingGroupOpts(), {"num_retries_to_skip": 5})
    pending_sessions = [
        gen_pending_for_holb_tests("s0", {}),
        gen_pending_for_holb_tests("s1", {}),
        gen_pending_for_holb_tests("s2", {}),
    ]
    picked_session_id = scheduler.pick_session(example_total_capacity, pending_sessions, [])
    assert picked_session_id == "s0"


def test_fifo_scheduler_hol_blocking_avoidance_config() -> None:
    """
    If the upfront sessions have enough number of retries,
    it should skip them.
    """
    scheduler = FIFOSlotScheduler(ScalingGroupOpts(), {"num_retries_to_skip": 0})
    pending_sessions = [
        gen_pending_for_holb_tests("s0", {"scheduler": {"retries": 5}}),
        gen_pending_for_holb_tests("s1", {}),
        gen_pending_for_holb_tests("s2", {}),
    ]
    picked_session_id = scheduler.pick_session(example_total_capacity, pending_sessions, [])
    assert picked_session_id == "s0"

    scheduler = FIFOSlotScheduler(ScalingGroupOpts(), {"num_retries_to_skip": 5})
    pending_sessions = [
        gen_pending_for_holb_tests("s0", {"scheduler": {"retries": 5}}),
        gen_pending_for_holb_tests("s1", {"scheduler": {"retries": 4}}),
        gen_pending_for_holb_tests("s2", {"scheduler": {"retries": 3}}),
    ]
    picked_session_id = scheduler.pick_session(example_total_capacity, pending_sessions, [])
    assert picked_session_id == "s1"


def test_fifo_scheduler_hol_blocking_avoidance_skips() -> None:
    """
    If the upfront sessions have enough number of retries,
    it should skip them.
    """
    scheduler = FIFOSlotScheduler(ScalingGroupOpts(), {"num_retries_to_skip": 5})
    pending_sessions = [
        gen_pending_for_holb_tests("s0", {"scheduler": {"retries": 5}}),
        gen_pending_for_holb_tests("s1", {}),
        gen_pending_for_holb_tests("s2", {}),
    ]
    picked_session_id = scheduler.pick_session(example_total_capacity, pending_sessions, [])
    assert picked_session_id == "s1"

    pending_sessions = [
        gen_pending_for_holb_tests("s0", {"scheduler": {"retries": 5}}),
        gen_pending_for_holb_tests("s1", {"scheduler": {"retries": 10}}),
        gen_pending_for_holb_tests("s2", {}),
    ]
    picked_session_id = scheduler.pick_session(example_total_capacity, pending_sessions, [])
    assert picked_session_id == "s2"


def test_fifo_scheduler_hol_blocking_avoidance_all_skipped() -> None:
    """
    If all sessions are skipped due to excessive number of retries,
    then we go back to the normal FIFO by choosing the first of them.
    """
    scheduler = FIFOSlotScheduler(ScalingGroupOpts(), {"num_retries_to_skip": 5})
    pending_sessions = [
        gen_pending_for_holb_tests("s0", {"scheduler": {"retries": 5}}),
        gen_pending_for_holb_tests("s1", {"scheduler": {"retries": 5}}),
        gen_pending_for_holb_tests("s2", {"scheduler": {"retries": 5}}),
    ]
    picked_session_id = scheduler.pick_session(example_total_capacity, pending_sessions, [])
    assert picked_session_id == "s0"


def test_fifo_scheduler_hol_blocking_avoidance_no_skip() -> None:
    """
    If non-first sessions have to be skipped, the scheduler should still
    choose the first session.
    """
    scheduler = FIFOSlotScheduler(ScalingGroupOpts(), {"num_retries_to_skip": 5})
    pending_sessions = [
        gen_pending_for_holb_tests("s0", {}),
        gen_pending_for_holb_tests("s1", {"scheduler": {"retries": 10}}),
        gen_pending_for_holb_tests("s2", {}),
    ]
    picked_session_id = scheduler.pick_session(example_total_capacity, pending_sessions, [])
    assert picked_session_id == "s0"


@pytest.mark.asyncio
async def test_lifo_scheduler_favor_cpu_for_requests_without_accelerators(
    example_mixed_agents: Sequence[AgentRow],
    example_pending_sessions: Sequence[SessionRow],
) -> None:
    # Check the reverse with the LIFO scheduler.
    # The result must be same.
    sgroup_opts = ScalingGroupOpts(agent_selection_strategy=AgentSelectionStrategy.DISPERSED)
    scheduler = LIFOSlotScheduler(sgroup_opts, {})
    agstate_cls = DispersedAgentSelector.get_state_cls()
    agselector = DispersedAgentSelector(
        sgroup_opts,
        {},
        agent_selection_resource_priority,
        state_store=InMemoryResourceGroupStateStore(agstate_cls),
    )
    total_capacity = sum((ag.available_slots for ag in example_mixed_agents), start=ResourceSlot())
    for idx in range(3):
        picked_session_id = scheduler.pick_session(total_capacity, example_pending_sessions, [])
        assert picked_session_id == example_pending_sessions[-1].id
        picked_session = _find_and_pop_picked_session(example_pending_sessions, picked_session_id)
        agent_id = await agselector.assign_agent_for_session(
            example_mixed_agents,
            picked_session,
        )
        if idx == 2:
            # example_mixed_agents do not have any agent with ROCM accelerators.
            assert agent_id is None
        elif idx == 1:
            assert agent_id == AgentId("i-gpu")
        elif idx == 0:
            # It should favor the CPU-only agent if the requested slots
            # do not include accelerators.
            assert agent_id == AgentId("i-cpu")


@pytest.mark.asyncio
async def test_drf_scheduler(
    example_agents: Sequence[AgentRow],
    example_pending_sessions: Sequence[SessionRow],
    example_existing_sessions: Sequence[SessionRow],
) -> None:
    sgroup_opts = ScalingGroupOpts(agent_selection_strategy=AgentSelectionStrategy.DISPERSED)
    scheduler = DRFScheduler(sgroup_opts, {})
    agstate_cls = DispersedAgentSelector.get_state_cls()
    agselector = DispersedAgentSelector(
        sgroup_opts,
        {},
        agent_selection_resource_priority,
        state_store=InMemoryResourceGroupStateStore(agstate_cls),
    )
    picked_session_id = scheduler.pick_session(
        sum((ag.available_slots for ag in example_agents), start=ResourceSlot()),
        example_pending_sessions,
        example_existing_sessions,
    )
    pprint(example_pending_sessions)
    assert picked_session_id == example_pending_sessions[1].id
    picked_session = _find_and_pop_picked_session(
        example_pending_sessions,
        picked_session_id,
    )
    agent_id = await agselector.assign_agent_for_session(
        example_agents,
        picked_session,
    )
    assert agent_id == "i-001"


@pytest.mark.asyncio
async def test_pending_timeout() -> None:
    class DummySession:
        def __init__(self, id, created_at, status) -> None:
            self.id = id
            self.created_at = created_at
            self.status = status

    now = datetime.now(tzutc())
    mock_query_result = MagicMock()
    mock_query_result.scalars = MagicMock()
    mock_query_result.scalars().all = MagicMock(
        return_value=[
            DummySession(
                id="session3",
                # created_at=datetime(2020, 12, 31, 23, 59, 59),
                created_at=now,
                status=SessionStatus.PENDING,
            ),
            DummySession(
                id="session2",
                # created_at=datetime(2020, 12, 30, 23, 59, 59),
                created_at=now - timedelta(seconds=86400),
                status=SessionStatus.PENDING,
            ),
            DummySession(
                id="session1",
                # created_at=datetime(2020, 12, 29, 23, 59, 59),
                created_at=now - timedelta(seconds=86400 * 3),
                status=SessionStatus.PENDING,
            ),
        ]
    )
    mock_dbsess = MagicMock()
    mock_dbsess.execute = AsyncMock(return_value=mock_query_result)

    scheduler = FIFOSlotScheduler(
        ScalingGroupOpts(pending_timeout=timedelta(seconds=86400 * 2)),
        {},
    )
    _, candidate_session_rows, cancelled_session_rows = await _list_managed_sessions(
        mock_dbsess,
        "default",
        pending_timeout=scheduler.sgroup_opts.pending_timeout,
    )
    assert len(candidate_session_rows) == 2
    assert len(cancelled_session_rows) == 1
    assert cancelled_session_rows[0].id == "session1"

    scheduler = FIFOSlotScheduler(
        ScalingGroupOpts(pending_timeout=timedelta(seconds=0)),
        {},
    )
    _, candidate_session_rows, cancelled_session_rows = await _list_managed_sessions(
        mock_dbsess,
        "default",
        pending_timeout=scheduler.sgroup_opts.pending_timeout,
    )
    assert len(candidate_session_rows) == 3
    assert len(cancelled_session_rows) == 0


class DummyEtcd:
    async def get_prefix(self, key: str) -> Mapping[str, Any]:
        return {}


@pytest.mark.asyncio
async def test_manually_assign_agent_available(
    file_lock_factory,
    registry_ctx: tuple[
        AgentRegistry, MagicMock, MagicMock, MagicMock, MagicMock, MagicMock, MagicMock
    ],
    mocker: pytest_mock.MockerFixture,
    example_agents: Sequence[AgentRow],
    example_pending_sessions: Sequence[SessionRow],
) -> None:
    mock_local_config = MagicMock()

    (
        registry,
        mock_dbconn,
        mock_dbsess,
        mock_dbresult,
        mock_shared_config,
        mock_event_dispatcher,
        mock_event_producer,
    ) = registry_ctx
    mock_sched_ctx = MagicMock()
    mock_check_result = MagicMock()
    mock_redis_wrapper = MagicMock()
    mock_redis_wrapper.execute = AsyncMock(return_value=[0 for _ in example_agents])
    mocker.patch("ai.backend.manager.scheduler.dispatcher.redis_helper", mock_redis_wrapper)
    sgroup_opts = ScalingGroupOpts()
    agstate_cls = DispersedAgentSelector.get_state_cls()
    agselector = DispersedAgentSelector(
        sgroup_opts,
        {},
        agent_selection_resource_priority,
        state_store=InMemoryResourceGroupStateStore(agstate_cls),
    )
    sgroup_name = example_agents[0].scaling_group
    candidate_agents = example_agents
    example_pending_sessions[0].kernels[0].agent = example_agents[0].id
    sess_ctx = example_pending_sessions[0]

    dispatcher = SchedulerDispatcher(
        local_config=mock_local_config,
        shared_config=mock_shared_config,
        event_dispatcher=mock_event_dispatcher,
        event_producer=mock_event_producer,
        lock_factory=file_lock_factory,
        registry=registry,
    )

    # manually assigned agent has None capacity
    mock_dbresult.scalar = MagicMock(return_value=None)
    await dispatcher._schedule_single_node_session(
        mock_sched_ctx,
        agselector,
        sgroup_name,
        candidate_agents,
        sess_ctx,
        mock_check_result,
    )
    result = mock_dbresult.scalar()
    assert result is None

    # manually assigned agent has empty capacity
    mock_dbresult.scalar = MagicMock(return_value={})
    await dispatcher._schedule_single_node_session(
        mock_sched_ctx,
        agselector,
        sgroup_name,
        candidate_agents,
        sess_ctx,
        mock_check_result,
    )
    result = mock_dbresult.scalar()
    assert result == {}

    # manually assigned agent is enough capacity
    mock_dbresult.scalar = MagicMock(
        return_value={
            "cpu": Decimal("8.0"),
            "mem": Decimal("8192"),
            "cuda.shares": Decimal("4"),
            "rocm.devices": Decimal("4"),
        }
    )
    await dispatcher._schedule_single_node_session(
        mock_sched_ctx,
        agselector,
        sgroup_name,
        candidate_agents,
        sess_ctx,
        mock_check_result,
    )
    result = mock_dbresult.scalar()
    for key in result:
        assert result[key] >= example_pending_sessions[0].requested_slots[key]

    # manually assigned agent is not enough capacity.
    mock_dbresult.scalar = MagicMock(
        return_value={
            "cpu": Decimal("0.0"),
            "mem": Decimal("0"),
            "cuda.shares": Decimal("0"),
            "rocm.devices": Decimal("0"),
        }
    )
    await dispatcher._schedule_single_node_session(
        mock_sched_ctx,
        agselector,
        sgroup_name,
        candidate_agents,
        sess_ctx,
        mock_check_result,
    )
    result = mock_dbresult.scalar()
    for key in result:
        assert result[key] <= example_pending_sessions[0].requested_slots[key]


@pytest.mark.asyncio
@mock.patch("ai.backend.manager.scheduler.predicates.datetime")
async def test_multiple_timezones_for_reserved_batch_session_predicate(mock_dt: MagicMock) -> None:
    mock_db_conn = MagicMock()
    mock_sched_ctx = MagicMock()
    mock_sess_ctx = MagicMock()
    mock_sess_ctx.session_type = SessionTypes.BATCH
    mock_sess_ctx.kernel_id = "fake-kernel-id"

    now = "2020-06-29T00:00:00+00:00"
    mock_dt.now = MagicMock(return_value=dtparse(now))

    # Start time is not yet reached (now < start time)
    start_time = "2020-06-29T00:00:01+00:00"
    mock_db_conn.scalar = AsyncMock(return_value=dtparse(start_time))
    result = await check_reserved_batch_session(mock_db_conn, mock_sched_ctx, mock_sess_ctx)
    assert not result.passed, (now, start_time)

    # Start time is reached (now > start time)
    start_time = "2020-06-28T23:59:59+00:00"
    mock_db_conn.scalar = AsyncMock(return_value=dtparse(start_time))
    result = await check_reserved_batch_session(mock_db_conn, mock_sched_ctx, mock_sess_ctx)
    assert result.passed, (now, start_time)

    # Start time is not yet reached by timezone (now < start time)
    # Note that 6/29 00:00 (UTC) < 6/29 00:00 (-09:00) == 6/29 09:00 (UTC)
    for i in range(1, 12):
        start_time = f"2020-06-29T00:00:00-{i:02d}:00"
        mock_db_conn.scalar = AsyncMock(return_value=dtparse(start_time))
        result = await check_reserved_batch_session(mock_db_conn, mock_sched_ctx, mock_sess_ctx)
        assert not result.passed, (now, start_time)

    # Start time is reached by timezone (now > start time)
    # Note that 6/29 00:00 (UTC) > 6/29 00:00 (+09:00) == 6/28 15:00 (UTC)
    for i in range(1, 12):
        start_time = f"2020-06-29T00:00:00+{i:02d}:00"
        mock_db_conn.scalar = AsyncMock(return_value=dtparse(start_time))
        result = await check_reserved_batch_session(mock_db_conn, mock_sched_ctx, mock_sess_ctx)
        assert result.passed, (now, start_time)

    # Should pass if start time is not specified (start immediately).
    mock_db_conn.scalar = AsyncMock(return_value=None)
    result = await check_reserved_batch_session(mock_db_conn, mock_sched_ctx, mock_sess_ctx)
    assert result.passed


@pytest.mark.asyncio
@pytest.mark.parametrize("example_agents_multi_homogeneous", [{"repeat": 10}], indirect=True)
@pytest.mark.parametrize("example_homogeneous_pending_sessions", [{"repeat": 20}], indirect=True)
async def test_agent_selection_strategy_rr(
    example_agents_multi_homogeneous: Sequence[AgentRow],
    example_homogeneous_pending_sessions: Sequence[SessionRow],
    example_existing_sessions: Sequence[SessionRow],
) -> None:
    sgroup_opts = ScalingGroupOpts(
        agent_selection_strategy=AgentSelectionStrategy.ROUNDROBIN,
    )
    scheduler = FIFOSlotScheduler(
        sgroup_opts,
        {},
    )

    agstate_cls = RoundRobinAgentSelector.get_state_cls()
    agselector = RoundRobinAgentSelector(
        sgroup_opts,
        {},
        agent_selection_resource_priority,
        state_store=InMemoryResourceGroupStateStore(agstate_cls),
    )

    num_agents = len(example_agents_multi_homogeneous)
    total_capacity = sum(
        (ag.available_slots for ag in example_agents_multi_homogeneous), ResourceSlot()
    )
    agent_ids = []
    # Repeat the allocation for two iterations
    for _ in range(num_agents * 2):
        picked_session_id = scheduler.pick_session(
            total_capacity,
            example_homogeneous_pending_sessions,
            example_existing_sessions,
        )
        assert picked_session_id == example_homogeneous_pending_sessions[0].id
        picked_session = _find_and_pop_picked_session(
            example_homogeneous_pending_sessions,
            picked_session_id,
        )
        agent_ids.append(
            await agselector.assign_agent_for_session(
                example_agents_multi_homogeneous,
                picked_session,
            )
        )
    assert agent_ids == [AgentId(f"i-{idx:03d}") for idx in range(num_agents)] * 2


@pytest.mark.asyncio
async def test_agent_selection_strategy_rr_skip_unacceptable_agents(
    example_agents_many: Sequence[AgentRow],
) -> None:
    # example_agents_many:
    # i-001: cpu=8, mem=4096, cuda.shares=4.0
    # i-002: cpu=4, mem=2048, cuda.shares=2.0
    # i-003: cpu=2, mem=1024, cuda.shares=1.0
    # i-004: cpu=1, mem=512,  cuda.shares=0.5
    agents: list[AgentRow] = [*example_agents_many]

    # all pending sessions:
    #        cpu=2, mem=500
    pending_sessions = [
        create_pending_session(
            SessionId(uuid4()),
            KernelId(uuid4()),
            ResourceSlot({
                "cpu": Decimal("2"),
                "mem": Decimal("500"),
            }),
        )
        for _ in range(8)
    ]

    sgroup_opts = ScalingGroupOpts(
        agent_selection_strategy=AgentSelectionStrategy.ROUNDROBIN,
    )
    scheduler = FIFOSlotScheduler(
        sgroup_opts,
        {},
    )

    agstate_cls = RoundRobinAgentSelector.get_state_cls()
    agselector = RoundRobinAgentSelector(
        sgroup_opts,
        {},
        agent_selection_resource_priority,
        state_store=InMemoryResourceGroupStateStore(agstate_cls),
    )

    total_capacity = sum((ag.available_slots for ag in agents), ResourceSlot())

    results: list[AgentId | None] = []
    scheduled_sessions: list[SessionRow] = []

    for _ in range(8):
        picked_session_id = scheduler.pick_session(
            total_capacity,
            pending_sessions,
            scheduled_sessions,
        )
        assert picked_session_id is not None
        picked_session = _find_and_pop_picked_session(
            pending_sessions,
            picked_session_id,
        )
        scheduled_sessions.append(picked_session)
        result = await agselector.assign_agent_for_session(
            agents,
            picked_session,
        )
        if result is not None:
            _update_agent_assignment(agents, result, picked_session.requested_slots)
        results.append(result)

    print()
    for ag in agents:
        print(
            ag.id,
            f"{ag.occupied_slots["cpu"]}/{ag.available_slots["cpu"]}",
            f"{ag.occupied_slots["mem"]}/{ag.available_slots["mem"]}",
        )
    # As more sessions have the assigned agents, the remaining capacity diminishes
    # and the range of round-robin also becomes limited.
    # When there is no assignable agent, it should return None.
    assert len(results) == 8
    assert results == ["i-001", "i-002", "i-003", "i-001", "i-002", "i-001", "i-001", None]
