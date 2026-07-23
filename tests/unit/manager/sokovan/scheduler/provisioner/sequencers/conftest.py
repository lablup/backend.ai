"""Local fixtures for sequencer tests.

Sequencers consume ``SessionWorkload`` and ``SystemSnapshot`` from
``ai.backend.manager.views.sokovan``; the factories below build minimal
instances of both.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable, Mapping
from decimal import Decimal

import pytest

from ai.backend.common.identifier.architecture import ArchName
from ai.backend.common.identifier.domain import DomainID
from ai.backend.common.identifier.project import ProjectID
from ai.backend.common.identifier.resource_group import ResourceGroupID
from ai.backend.common.identifier.resource_slot import ResourceSlotName
from ai.backend.common.identifier.user import UserID
from ai.backend.common.types import (
    AccessKey,
    AgentId,
    AgentSelectionStrategy,
    ClusterMode,
    KernelId,
    SessionId,
    SessionTypes,
)
from ai.backend.manager.data.session.options import AgentSelectionPolicy
from ai.backend.manager.views.sokovan.agent import (
    AgentLimit,
    AgentMeta,
    AgentResource,
    ResourceGroupResource,
    SlotResource,
)
from ai.backend.manager.views.sokovan.snapshot import (
    GlobalScopeSnapshot,
    ResourceGroupSchedulingPolicy,
    ResourceGroupScopeSnapshot,
    ResourceOccupancySnapshot,
    ResourcePolicySnapshot,
    SessionDependencySnapshot,
    SlotAllocation,
    SystemSnapshot,
    UserResourceAllocation,
)
from ai.backend.manager.views.sokovan.workload import (
    KernelWorkload,
    ResourceRequest,
    SessionPlacement,
    SessionWorkload,
    WorkloadMeta,
    WorkloadOwner,
)

RESOURCE_GROUP_ID = ResourceGroupID(uuid.UUID(int=0))

WorkloadFactory = Callable[..., SessionWorkload]
SnapshotFactory = Callable[..., SystemSnapshot]


def _make_workload(
    *,
    user_id: UserID | None = None,
    priority: int = 0,
    slots: Mapping[str, str] | None = None,
    session_type: SessionTypes = SessionTypes.INTERACTIVE,
) -> SessionWorkload:
    if user_id is None:
        user_id = UserID(uuid.uuid4())
    if slots is None:
        slots = {"cpu": "1", "mem": "1024"}
    return SessionWorkload(
        meta=WorkloadMeta(
            session_id=SessionId(uuid.uuid4()),
            resource_group_id=RESOURCE_GROUP_ID,
            owner=WorkloadOwner(
                access_key=AccessKey("AKTEST"),
                user_uuid=user_id,
                project_id=ProjectID(uuid.UUID(int=1)),
                domain_id=DomainID(uuid.UUID(int=2)),
            ),
        ),
        placement=SessionPlacement(
            cluster_mode=ClusterMode.SINGLE_NODE,
            kernels=[
                KernelWorkload(
                    kernel_id=KernelId(uuid.uuid4()),
                    architecture=ArchName("x86_64"),
                    requested_slots=ResourceRequest(
                        slots={
                            ResourceSlotName(name): Decimal(amount)
                            for name, amount in slots.items()
                        }
                    ),
                )
            ],
            agent_selection_policy=AgentSelectionPolicy.STRICT,
            designated_agent_ids=None,
        ),
        priority=priority,
        job_priority=0,
        session_type=session_type,
        starts_at=None,
        is_preemptible=False,
    )


def _make_snapshot(
    *,
    capacities: Mapping[str, str] | None = None,
    by_user: Mapping[UserID, Mapping[str, tuple[str, str]]] | None = None,
    scheduler: str = "fifo",
) -> SystemSnapshot:
    """Build a snapshot with one agent of the given capacities and the given
    per-user occupancy (slot -> (requested, used))."""
    if capacities is None:
        capacities = {"cpu": "100", "mem": "102400"}
    occupancy_by_user = {
        user_id: UserResourceAllocation(
            slots={
                ResourceSlotName(name): SlotAllocation(
                    requested=Decimal(requested), used=Decimal(used)
                )
                for name, (requested, used) in slots.items()
            },
            session_count=0,
            sftp_session_count=0,
        )
        for user_id, slots in (by_user or {}).items()
    }
    return SystemSnapshot(
        resource_group=ResourceGroupScopeSnapshot(
            resources=ResourceGroupResource(
                agents=[
                    AgentMeta(
                        id=AgentId("agent-1"),
                        addr="agent-1:6001",
                        architecture=ArchName("x86_64"),
                        resources=AgentResource(
                            slots={
                                ResourceSlotName(name): SlotResource(
                                    capacity=Decimal(amount),
                                    reserved=Decimal(0),
                                    used=Decimal(0),
                                )
                                for name, amount in capacities.items()
                            }
                        ),
                        container_count=0,
                    )
                ],
            ),
            session_dependencies=SessionDependencySnapshot(by_session={}),
            policy=ResourceGroupSchedulingPolicy(
                scheduler=scheduler,
                agent_selection_strategy=AgentSelectionStrategy.CONCENTRATED,
            ),
        ),
        global_scope=GlobalScopeSnapshot(
            occupancy=ResourceOccupancySnapshot(
                by_user=occupancy_by_user,
                by_project={},
                by_domain={},
            ),
            resource_policy=ResourcePolicySnapshot(by_user={}, by_project={}, by_domain={}),
            agent_limit=AgentLimit(max_container_count=None),
        ),
    )


@pytest.fixture
def workload_factory() -> WorkloadFactory:
    return _make_workload


@pytest.fixture
def snapshot_factory() -> SnapshotFactory:
    return _make_snapshot


@pytest.fixture
def empty_snapshot() -> SystemSnapshot:
    return _make_snapshot()
