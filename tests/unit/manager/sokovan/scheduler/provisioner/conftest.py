"""Local fixtures for provisioner-level tests.

Builds ``SchedulingData`` bundles from the current view types; the parent
scheduler conftest targets other scheduler layers.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable, Mapping
from decimal import Decimal

import pytest

from ai.backend.common.identifier.architecture import ArchName
from ai.backend.common.identifier.domain import DomainID
from ai.backend.common.identifier.project import ProjectID
from ai.backend.common.identifier.resource_group import ResourceGroupID, ResourceGroupName
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
from ai.backend.manager.views.sokovan.resource_group import ResourceGroupMeta
from ai.backend.manager.views.sokovan.scheduling import SchedulingData
from ai.backend.manager.views.sokovan.snapshot import (
    GlobalScopeSnapshot,
    ResourceGroupSchedulingPolicy,
    ResourceGroupScopeSnapshot,
    ResourceOccupancySnapshot,
    ResourcePolicySnapshot,
    SessionDependencySnapshot,
    SystemSnapshot,
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
RESOURCE_GROUP_NAME = ResourceGroupName("default")

WorkloadFactory = Callable[..., SessionWorkload]
AgentMetaFactory = Callable[..., AgentMeta]
SchedulingDataFactory = Callable[..., SchedulingData]


def _make_workload(
    *,
    kernel_slots: list[Mapping[str, str]] | None = None,
    priority: int = 0,
    cluster_mode: ClusterMode = ClusterMode.SINGLE_NODE,
) -> SessionWorkload:
    if kernel_slots is None:
        kernel_slots = [{"cpu": "1", "mem": "1024"}]
    return SessionWorkload(
        meta=WorkloadMeta(
            session_id=SessionId(uuid.uuid4()),
            resource_group_id=RESOURCE_GROUP_ID,
            owner=WorkloadOwner(
                access_key=AccessKey("AKTEST"),
                user_uuid=UserID(uuid.uuid4()),
                project_id=ProjectID(uuid.UUID(int=1)),
                domain_id=DomainID(uuid.UUID(int=2)),
            ),
        ),
        placement=SessionPlacement(
            cluster_mode=cluster_mode,
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
                for slots in kernel_slots
            ],
            agent_selection_policy=AgentSelectionPolicy.STRICT,
            designated_agent_ids=None,
        ),
        priority=priority,
        job_priority=0,
        session_type=SessionTypes.INTERACTIVE,
        starts_at=None,
        is_preemptible=False,
    )


def _make_agent_meta(
    agent_id: str = "agent-1",
    capacities: Mapping[str, str] | None = None,
) -> AgentMeta:
    if capacities is None:
        capacities = {"cpu": "16", "mem": "32768"}
    return AgentMeta(
        id=AgentId(agent_id),
        addr=f"{agent_id}:6001",
        architecture=ArchName("x86_64"),
        resources=AgentResource(
            slots={
                ResourceSlotName(name): SlotResource(
                    capacity=Decimal(amount), reserved=Decimal(0), used=Decimal(0)
                )
                for name, amount in capacities.items()
            }
        ),
        container_count=0,
    )


def _make_scheduling_data(
    *,
    workloads: list[SessionWorkload],
    agents: list[AgentMeta] | None = None,
    scheduler: str = "fifo",
    agent_selection_strategy: AgentSelectionStrategy = AgentSelectionStrategy.CONCENTRATED,
) -> SchedulingData:
    if agents is None:
        agents = [_make_agent_meta()]
    return SchedulingData(
        resource_group=ResourceGroupMeta(id=RESOURCE_GROUP_ID, name=RESOURCE_GROUP_NAME),
        workloads=workloads,
        system_snapshot=SystemSnapshot(
            resource_group=ResourceGroupScopeSnapshot(
                resources=ResourceGroupResource(agents=agents),
                session_dependencies=SessionDependencySnapshot(by_session={}),
                policy=ResourceGroupSchedulingPolicy(
                    scheduler=scheduler,
                    agent_selection_strategy=agent_selection_strategy,
                ),
            ),
            global_scope=GlobalScopeSnapshot(
                occupancy=ResourceOccupancySnapshot(by_user={}, by_project={}, by_domain={}),
                resource_policy=ResourcePolicySnapshot(by_user={}, by_project={}, by_domain={}),
                agent_limit=AgentLimit(max_container_count=None),
            ),
        ),
    )


@pytest.fixture
def workload_factory() -> WorkloadFactory:
    return _make_workload


@pytest.fixture
def agent_meta_factory() -> AgentMetaFactory:
    return _make_agent_meta


@pytest.fixture
def scheduling_data_factory() -> SchedulingDataFactory:
    return _make_scheduling_data
