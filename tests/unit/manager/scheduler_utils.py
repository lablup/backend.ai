from __future__ import annotations

import secrets
from collections.abc import (
    Iterator,
    Mapping,
    Sequence,
)
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import (
    Any,
    Final,
)
from uuid import uuid4

from dateutil.parser import parse as dtparse

from ai.backend.common.defs.session import SESSION_PRIORITY_DEFAULT
from ai.backend.common.docker import ImageRef
from ai.backend.common.types import (
    AccessKey,
    AgentId,
    KernelId,
    ResourceSlot,
    SessionId,
    SessionTypes,
)
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.defs import DEFAULT_ROLE
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.session import SessionRow

ARCH_FOR_TEST: Final = "x86_64"

agent_selection_resource_priority: Final = ["cuda", "rocm", "tpu", "cpu", "mem"]

common_image_ref: Final = ImageRef(
    name="python",
    project="lablup",
    tag="3.6-ubuntu18.04",
    registry="index.docker.io",
    architecture=ARCH_FOR_TEST,
    is_local=False,
)

example_group_id = uuid4()
example_total_capacity = ResourceSlot({"cpu": "4.0", "mem": "4096"})
example_sgroup_name1: Final = "sg01"
example_sgroup_name2: Final = "sg02"

_common_dummy_for_pending_session: Mapping[str, Any] = dict(
    domain_name="default",
    group_id=example_group_id,
    vfolder_mounts=[],
    environ={},
    bootstrap_script=None,
    startup_command=None,
    use_host_network=False,
)

_timestamp_count = 0


def generate_timestamp() -> datetime:
    global _timestamp_count
    val = dtparse("2021-12-28T23:59:59+00:00")
    val += timedelta(_timestamp_count * 10)
    _timestamp_count += 1
    return val


def generate_role() -> Iterator[tuple[str, int, int]]:
    yield ("main", 1, 0)
    sub_idx = 1
    while True:
        yield ("sub", sub_idx, sub_idx)
        sub_idx += 1


@dataclass
class KernelOpt:
    requested_slots: ResourceSlot
    kernel_id: KernelId = field(default_factory=lambda: KernelId(uuid4()))
    image: ImageRef = common_image_ref


_sess_kern_status_map = {
    SessionStatus.PENDING: KernelStatus.PENDING,
    SessionStatus.SCHEDULED: KernelStatus.SCHEDULED,
    SessionStatus.RUNNING: KernelStatus.RUNNING,
    SessionStatus.TERMINATED: KernelStatus.TERMINATED,
}


def find_and_pop_picked_session(pending_sessions, picked_session_id) -> SessionRow:
    for picked_idx, pending_sess in enumerate(pending_sessions):
        if pending_sess.id == picked_session_id:
            break
    else:
        # no matching entry for picked session?
        raise RuntimeError("should not reach here")
    return pending_sessions.pop(picked_idx)


def update_agent_assignment(
    agents: Sequence[AgentRow],
    picked_agent_id: AgentId,
    occupied_slots: ResourceSlot,
) -> None:
    for ag in agents:
        if ag.id == picked_agent_id:
            ag.occupied_slots += occupied_slots


def create_mock_kernel(
    session_id: SessionId,
    kernel_id: KernelId,
    requested_slots: ResourceSlot,
    *,
    status: KernelStatus = KernelStatus.PENDING,
    cluster_role: str = DEFAULT_ROLE,
    cluster_idx: int = 1,
    local_rank: int = 0,
) -> KernelRow:
    return KernelRow(
        id=session_id,
        session_id=kernel_id,
        status=status,
        access_key="dummy-access-key",
        agent=None,
        agent_addr=None,
        cluster_role=cluster_role,
        cluster_idx=cluster_idx,
        local_rank=local_rank,
        cluster_hostname=f"{cluster_role}{cluster_idx}",
        architecture=common_image_ref.architecture,
        registry=common_image_ref.registry,
        image=common_image_ref.name,
        requested_slots=requested_slots,
        bootstrap_script=None,
        startup_command=None,
        created_at=generate_timestamp(),
    )


def create_mock_session(
    session_id: SessionId,
    requested_slots: ResourceSlot,
    *,
    access_key: AccessKey = AccessKey("user01"),
    status: SessionStatus = SessionStatus.PENDING,
    status_data: dict[str, Any] | None = None,
    kernel_opts: Sequence[KernelOpt] | None = None,
    priority: int = SESSION_PRIORITY_DEFAULT,
    session_type: SessionTypes = SessionTypes.BATCH,
) -> SessionRow:
    """Create a simple single-kernel pending session."""
    if kernel_opts is None:
        # Create a single pending kernel as a default
        kernel_opts = [KernelOpt(requested_slots=requested_slots)]
    return SessionRow(
        kernels=[
            create_mock_kernel(
                session_id,
                kopt.kernel_id,
                kopt.requested_slots,
                status=_sess_kern_status_map[status],
                cluster_role=role_name,
                cluster_idx=role_idx,
                local_rank=local_rank,
            )
            for kopt, (role_name, role_idx, local_rank) in zip(kernel_opts, generate_role())
        ],
        priority=priority,
        access_key=access_key,
        id=session_id,
        creation_id=secrets.token_hex(8),
        name=f"session-{secrets.token_hex(4)}",
        session_type=session_type,
        status=status,
        status_data=status_data,
        cluster_mode="single-node",
        cluster_size=len(kernel_opts),
        scaling_group_name=example_sgroup_name1,
        requested_slots=requested_slots,
        occupying_slots=(
            requested_slots
            if status not in (SessionStatus.PENDING, SessionStatus.SCHEDULED)
            else ResourceSlot()
        ),
        target_sgroup_names=[],
        **_common_dummy_for_pending_session,
        created_at=generate_timestamp(),
    )


def create_mock_agent(
    id: AgentId,
    *,
    scaling_group: str = example_sgroup_name1,
    available_slots: ResourceSlot,
    occupied_slots: ResourceSlot = ResourceSlot(),
) -> AgentRow:
    return AgentRow(
        id=id,
        addr="10.0.1.1:6001",
        architecture=ARCH_FOR_TEST,
        scaling_group=scaling_group,
        available_slots=available_slots,
        occupied_slots=occupied_slots,
    )
