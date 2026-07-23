"""Common fixtures for sokovan scheduler tests."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from dateutil.tz import tzutc

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
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.session.options import AgentSelectionPolicy
from ai.backend.manager.data.session.types import (
    SessionStatus,
    StatusTransitions,
    TransitionStatus,
)
from ai.backend.manager.views.sokovan.agent import (
    AgentLimit,
    ResourceGroupResource,
)
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

# =============================================================================
# Factory helpers
# =============================================================================


def create_kernel_workload(
    *,
    kernel_id: KernelId | None = None,
    architecture: str = "x86_64",
    slots: Mapping[str, Decimal] | None = None,
) -> KernelWorkload:
    """Create a KernelWorkload for testing."""
    if slots is None:
        slots = {"cpu": Decimal(1), "mem": Decimal(1)}
    return KernelWorkload(
        kernel_id=kernel_id or KernelId(uuid4()),
        architecture=ArchName(architecture),
        requested_slots=ResourceRequest(
            slots={ResourceSlotName(name): amount for name, amount in slots.items()}
        ),
    )


def create_session_workload(
    *,
    session_id: SessionId | None = None,
    resource_group_id: ResourceGroupID | None = None,
    access_key: str = "test-key",
    user_uuid: UserID | None = None,
    project_id: ProjectID | None = None,
    domain_id: DomainID | None = None,
    cluster_mode: ClusterMode = ClusterMode.SINGLE_NODE,
    kernels: list[KernelWorkload] | None = None,
    slots: Mapping[str, Decimal] | None = None,
    agent_selection_policy: AgentSelectionPolicy = AgentSelectionPolicy.PREFERRED,
    designated_agent_ids: list[AgentId] | None = None,
    priority: int = 0,
    job_priority: int = 0,
    session_type: SessionTypes = SessionTypes.INTERACTIVE,
    starts_at: datetime | None = None,
    is_preemptible: bool = False,
) -> SessionWorkload:
    """Create a SessionWorkload for testing.

    ``requested_slots`` is derived from the kernels; pass ``slots`` to get a
    single-kernel workload requesting exactly those amounts.
    """
    if kernels is None:
        kernels = [create_kernel_workload(slots=slots)]
    return SessionWorkload(
        meta=WorkloadMeta(
            session_id=session_id or SessionId(uuid4()),
            resource_group_id=resource_group_id or ResourceGroupID(uuid4()),
            owner=WorkloadOwner(
                access_key=AccessKey(access_key),
                user_uuid=user_uuid or UserID(uuid4()),
                project_id=project_id or ProjectID(uuid4()),
                domain_id=domain_id or DomainID(uuid4()),
            ),
        ),
        placement=SessionPlacement(
            cluster_mode=cluster_mode,
            kernels=kernels,
            agent_selection_policy=agent_selection_policy,
            designated_agent_ids=designated_agent_ids,
        ),
        priority=priority,
        job_priority=job_priority,
        session_type=session_type,
        starts_at=starts_at,
        is_preemptible=is_preemptible,
    )


def create_system_snapshot(
    *,
    resources: ResourceGroupResource | None = None,
    session_dependencies: SessionDependencySnapshot | None = None,
    scheduler: str = "fifo",
    agent_selection_strategy: AgentSelectionStrategy = AgentSelectionStrategy.CONCENTRATED,
    occupancy: ResourceOccupancySnapshot | None = None,
    resource_policy: ResourcePolicySnapshot | None = None,
    max_container_count: int | None = None,
) -> SystemSnapshot:
    """Create a SystemSnapshot for testing."""
    return SystemSnapshot(
        resource_group=ResourceGroupScopeSnapshot(
            resources=resources or ResourceGroupResource(agents=[]),
            session_dependencies=session_dependencies or SessionDependencySnapshot(by_session={}),
            policy=ResourceGroupSchedulingPolicy(
                scheduler=scheduler,
                agent_selection_strategy=agent_selection_strategy,
            ),
        ),
        global_scope=GlobalScopeSnapshot(
            occupancy=occupancy
            or ResourceOccupancySnapshot(by_user={}, by_project={}, by_domain={}),
            resource_policy=resource_policy
            or ResourcePolicySnapshot(by_user={}, by_project={}, by_domain={}),
            agent_limit=AgentLimit(max_container_count=max_container_count),
        ),
    )


# =============================================================================
# Workload fixtures
# =============================================================================


@pytest.fixture
def basic_session_workload() -> SessionWorkload:
    """Basic SessionWorkload instance with default values."""
    return create_session_workload()


@pytest.fixture
def batch_session_workload() -> SessionWorkload:
    """Batch SessionWorkload instance."""
    return create_session_workload(session_type=SessionTypes.BATCH)


@pytest.fixture
def inference_session_workload() -> SessionWorkload:
    """Inference SessionWorkload instance."""
    return create_session_workload(session_type=SessionTypes.INFERENCE)


@pytest.fixture
def minimal_resource_workload() -> SessionWorkload:
    """SessionWorkload with minimal resource requirements (1 CPU, 1 mem)."""
    return create_session_workload(access_key="user1", slots={"cpu": Decimal(1), "mem": Decimal(1)})


@pytest.fixture
def small_resource_workload() -> SessionWorkload:
    """SessionWorkload with small resource requirements."""
    return create_session_workload(access_key="user1", slots={"cpu": Decimal(2), "mem": Decimal(2)})


@pytest.fixture
def medium_resource_workload() -> SessionWorkload:
    """SessionWorkload with medium resource requirements."""
    return create_session_workload(access_key="user1", slots={"cpu": Decimal(5), "mem": Decimal(5)})


@pytest.fixture
def large_resource_workload() -> SessionWorkload:
    """SessionWorkload with large resource requirements."""
    return create_session_workload(
        access_key="user1", slots={"cpu": Decimal(100), "mem": Decimal(100)}
    )


@pytest.fixture
def test_domain_id() -> DomainID:
    """Test domain ID for use in tests."""
    return DomainID(uuid4())


@pytest.fixture
def test_domain_small_resource_workload(test_domain_id: DomainID) -> SessionWorkload:
    """SessionWorkload with small resources for domain testing."""
    return create_session_workload(
        access_key="user1",
        domain_id=test_domain_id,
        slots={"cpu": Decimal(2), "mem": Decimal(2)},
    )


@pytest.fixture
def test_domain_medium_resource_workload(test_domain_id: DomainID) -> SessionWorkload:
    """SessionWorkload with medium resources for domain testing."""
    return create_session_workload(
        access_key="user1",
        domain_id=test_domain_id,
        slots={"cpu": Decimal(5), "mem": Decimal(5)},
    )


@pytest.fixture
def test_domain_large_resource_workload(test_domain_id: DomainID) -> SessionWorkload:
    """SessionWorkload with large resources for domain testing."""
    return create_session_workload(
        access_key="user1",
        domain_id=test_domain_id,
        slots={"cpu": Decimal(100), "mem": Decimal(100)},
    )


@pytest.fixture
def user1_minimal_workload() -> SessionWorkload:
    """Minimal workload for user1."""
    return create_session_workload(access_key="user1", slots={"cpu": Decimal(1), "mem": Decimal(1)})


@pytest.fixture
def test_user_id() -> UserID:
    """Test user ID for use in tests."""
    return UserID(uuid4())


@pytest.fixture
def user_specific_small_workload(test_user_id: UserID) -> SessionWorkload:
    """Small workload for a specific user."""
    return create_session_workload(
        access_key="user1", user_uuid=test_user_id, slots={"cpu": Decimal(2), "mem": Decimal(2)}
    )


@pytest.fixture
def user_specific_medium_workload(test_user_id: UserID) -> SessionWorkload:
    """Medium workload for a specific user."""
    return create_session_workload(
        access_key="user1", user_uuid=test_user_id, slots={"cpu": Decimal(5), "mem": Decimal(5)}
    )


@pytest.fixture
def user_specific_minimal_workload(test_user_id: UserID) -> SessionWorkload:
    """Minimal workload for a specific user."""
    return create_session_workload(
        access_key="user1", user_uuid=test_user_id, slots={"cpu": Decimal(1), "mem": Decimal(1)}
    )


@pytest.fixture
def batch_session_past_start_time() -> SessionWorkload:
    """Batch session with start time in the past."""
    past_time = datetime.now(tzutc()) - timedelta(hours=1)
    return create_session_workload(session_type=SessionTypes.BATCH, starts_at=past_time)


@pytest.fixture
def batch_session_future_start_time() -> SessionWorkload:
    """Batch session with start time in the future."""
    future_time = datetime.now(tzutc()) + timedelta(hours=1)
    return create_session_workload(session_type=SessionTypes.BATCH, starts_at=future_time)


# =============================================================================
# Coordinator test fixtures
# =============================================================================


@pytest.fixture
def status_transitions_with_all_outcomes() -> StatusTransitions:
    """StatusTransitions with all outcome types defined."""
    return StatusTransitions(
        success=TransitionStatus(session=SessionStatus.SCHEDULED, kernel=KernelStatus.SCHEDULED),
        need_retry=TransitionStatus(session=SessionStatus.PENDING, kernel=KernelStatus.PENDING),
        expired=TransitionStatus(session=SessionStatus.CANCELLED, kernel=KernelStatus.CANCELLED),
        give_up=TransitionStatus(session=SessionStatus.CANCELLED, kernel=KernelStatus.CANCELLED),
    )


@pytest.fixture
def status_transitions_success_only() -> StatusTransitions:
    """StatusTransitions with only success outcome."""
    return StatusTransitions(
        success=TransitionStatus(session=SessionStatus.SCHEDULED, kernel=KernelStatus.SCHEDULED),
        need_retry=None,
        expired=None,
        give_up=None,
    )


# =============================================================================
# Snapshot fixtures
# =============================================================================


@pytest.fixture
def empty_system_snapshot() -> SystemSnapshot:
    """Create an empty system snapshot for testing."""
    return create_system_snapshot()


__all__ = [
    "create_kernel_workload",
    "create_session_workload",
    "create_system_snapshot",
]
