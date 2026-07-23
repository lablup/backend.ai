"""Local fixtures for validator tests.

Validators consume ``SystemSnapshot`` + ``SessionWorkload``; the factories
below build minimal instances with a fixed owner so limits and occupancy can
be attached to the workload's scopes.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable, Mapping
from datetime import UTC, datetime
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
    AgentSelectionStrategy,
    ClusterMode,
    KernelId,
    SessionId,
    SessionTypes,
)
from ai.backend.manager.data.session.options import AgentSelectionPolicy
from ai.backend.manager.views.sokovan.agent import AgentLimit, ResourceGroupResource
from ai.backend.manager.views.sokovan.snapshot import (
    GlobalScopeSnapshot,
    ResourceAllocation,
    ResourceGroupSchedulingPolicy,
    ResourceGroupScopeSnapshot,
    ResourceLimit,
    ResourceOccupancySnapshot,
    ResourcePolicySnapshot,
    SessionDependencySnapshot,
    SlotAllocation,
    SystemSnapshot,
    UserResourceAllocation,
    UserResourceLimit,
)
from ai.backend.manager.views.sokovan.workload import (
    KernelWorkload,
    ResourceRequest,
    SessionDependencyInfo,
    SessionPlacement,
    SessionWorkload,
    WorkloadMeta,
    WorkloadOwner,
)

RESOURCE_GROUP_ID = ResourceGroupID(uuid.UUID(int=0))
USER_ID = UserID(uuid.UUID(int=101))
PROJECT_ID = ProjectID(uuid.UUID(int=102))
DOMAIN_ID = DomainID(uuid.UUID(int=103))

WorkloadFactory = Callable[..., SessionWorkload]
SnapshotFactory = Callable[..., SystemSnapshot]

# Re-exported building blocks for per-test snapshot composition
__all__ = [
    "RESOURCE_GROUP_ID",
    "USER_ID",
    "PROJECT_ID",
    "DOMAIN_ID",
    "WorkloadFactory",
    "SnapshotFactory",
]


def slot_map(slots: Mapping[str, str]) -> dict[ResourceSlotName, Decimal]:
    return {ResourceSlotName(name): Decimal(amount) for name, amount in slots.items()}


def _make_workload(
    *,
    session_id: SessionId | None = None,
    slots: Mapping[str, str] | None = None,
    session_type: SessionTypes = SessionTypes.INTERACTIVE,
    requested_starts_at: datetime | None = None,
) -> SessionWorkload:
    if session_id is None:
        session_id = SessionId(uuid.uuid4())
    if slots is None:
        slots = {"cpu": "2", "mem": "4096"}
    return SessionWorkload(
        meta=WorkloadMeta(
            session_id=session_id,
            resource_group_id=RESOURCE_GROUP_ID,
            owner=WorkloadOwner(
                access_key=AccessKey("AKTEST"),
                user_uuid=USER_ID,
                project_id=PROJECT_ID,
                domain_id=DOMAIN_ID,
            ),
        ),
        placement=SessionPlacement(
            cluster_mode=ClusterMode.SINGLE_NODE,
            kernels=[
                KernelWorkload(
                    kernel_id=KernelId(uuid.uuid4()),
                    architecture=ArchName("x86_64"),
                    requested_slots=ResourceRequest(slots=slot_map(slots)),
                )
            ],
            agent_selection_policy=AgentSelectionPolicy.STRICT,
            designated_agent_ids=None,
        ),
        priority=0,
        job_priority=0,
        session_type=session_type,
        requested_starts_at=requested_starts_at,
        is_preemptible=False,
    )


def _make_snapshot(
    *,
    dependencies: Mapping[SessionId, list[SessionDependencyInfo]] | None = None,
    user_limit: UserResourceLimit | None = None,
    project_limit: ResourceLimit | None = None,
    domain_limit: ResourceLimit | None = None,
    occupancy: ResourceOccupancySnapshot | None = None,
    observed_at: datetime | None = None,
) -> SystemSnapshot:
    if occupancy is None:
        occupancy = ResourceOccupancySnapshot(by_user={}, by_project={}, by_domain={})
    return SystemSnapshot(
        resource_group=ResourceGroupScopeSnapshot(
            resources=ResourceGroupResource(agents=[]),
            session_dependencies=SessionDependencySnapshot(by_session=dict(dependencies or {})),
            policy=ResourceGroupSchedulingPolicy(
                scheduler="fifo",
                agent_selection_strategy=AgentSelectionStrategy.CONCENTRATED,
            ),
        ),
        global_scope=GlobalScopeSnapshot(
            occupancy=occupancy,
            resource_policy=ResourcePolicySnapshot(
                by_user={USER_ID: user_limit} if user_limit is not None else {},
                by_project={PROJECT_ID: project_limit} if project_limit is not None else {},
                by_domain={DOMAIN_ID: domain_limit} if domain_limit is not None else {},
            ),
            agent_limit=AgentLimit(max_container_count=None),
        ),
        observed_at=observed_at if observed_at is not None else datetime.now(UTC),
    )


def user_allocation_snapshot(
    *,
    user_slots: Mapping[str, tuple[str, str]] | None = None,
    session_count: int = 0,
    sftp_session_count: int = 0,
    project_slots: Mapping[str, tuple[str, str]] | None = None,
    domain_slots: Mapping[str, tuple[str, str]] | None = None,
) -> ResourceOccupancySnapshot:
    """Build occupancy for the fixed owner; slot values are (requested, used)."""

    def _alloc(slots: Mapping[str, tuple[str, str]]) -> dict[ResourceSlotName, SlotAllocation]:
        return {
            ResourceSlotName(name): SlotAllocation(requested=Decimal(requested), used=Decimal(used))
            for name, (requested, used) in slots.items()
        }

    return ResourceOccupancySnapshot(
        by_user={
            USER_ID: UserResourceAllocation(
                slots=_alloc(user_slots or {}),
                session_count=session_count,
                sftp_session_count=sftp_session_count,
            )
        },
        by_project=(
            {PROJECT_ID: ResourceAllocation(slots=_alloc(project_slots))}
            if project_slots is not None
            else {}
        ),
        by_domain=(
            {DOMAIN_ID: ResourceAllocation(slots=_alloc(domain_slots))}
            if domain_slots is not None
            else {}
        ),
    )


@pytest.fixture
def workload_factory() -> WorkloadFactory:
    return _make_workload


@pytest.fixture
def snapshot_factory() -> SnapshotFactory:
    return _make_snapshot


@pytest.fixture
def occupancy_factory() -> Callable[..., ResourceOccupancySnapshot]:
    return user_allocation_snapshot
