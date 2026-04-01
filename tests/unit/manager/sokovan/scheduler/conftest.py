"""Common fixtures for sokovan scheduler tests."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from dateutil.tz import tzutc

from ai.backend.common.types import (
    AccessKey,
    ClusterMode,
    ResourceSlot,
    SessionId,
    SessionTypes,
)
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.session.types import (
    SessionStatus,
    StatusTransitions,
    TransitionStatus,
)
from ai.backend.manager.sokovan.data import (
    ConcurrencySnapshot,
    PendingSessionSnapshot,
    ResourceOccupancySnapshot,
    ResourcePolicySnapshot,
    SessionDependencySnapshot,
    SessionWorkload,
    SystemSnapshot,
)
from ai.backend.manager.sokovan.scheduler.results import (
    SessionExecutionResult,
    SessionTransitionInfo,
)


def _create_mock_session_with_kernels(
    session_id: SessionId,
    scaling_group: str = "default",
    status: SessionStatus = SessionStatus.PREPARING,
) -> MagicMock:
    """Create a mock SessionWithKernels with nested attributes properly set."""
    mock = MagicMock()
    mock.session_info.identity.id = session_id
    mock.session_info.identity.creation_id = str(uuid4())
    mock.session_info.metadata.access_key = AccessKey("test-key")
    mock.session_info.resource.scaling_group_name = scaling_group
    mock.session_info.lifecycle.status = status
    mock.session_id = session_id
    mock.status = status
    mock.scaling_group = scaling_group
    mock.kernel_infos = []
    return mock


@pytest.fixture
def sessions_for_multi_scaling_group_iteration() -> tuple[MagicMock, MagicMock, MagicMock]:
    """Three sessions in different scaling groups for testing scaling group iteration."""
    return (
        _create_mock_session_with_kernels(SessionId(uuid4()), "sg1"),
        _create_mock_session_with_kernels(SessionId(uuid4()), "sg2"),
        _create_mock_session_with_kernels(SessionId(uuid4()), "sg3"),
    )


@pytest.fixture
def session_for_post_process_verification() -> MagicMock:
    """Single session for verifying post_process callback behavior."""
    return _create_mock_session_with_kernels(SessionId(uuid4()), "default")


@pytest.fixture
def sessions_for_parallel_processing_with_error() -> tuple[MagicMock, MagicMock, MagicMock]:
    """Three sessions for testing parallel processing where one fails."""
    return (
        _create_mock_session_with_kernels(SessionId(uuid4()), "sg1"),
        _create_mock_session_with_kernels(SessionId(uuid4()), "sg2"),
        _create_mock_session_with_kernels(SessionId(uuid4()), "sg3"),
    )


@pytest.fixture
def sessions_for_independent_scaling_group_processing() -> tuple[MagicMock, MagicMock]:
    """Two sessions for testing independent processing per scaling group."""
    return (
        _create_mock_session_with_kernels(SessionId(uuid4()), "sg1"),
        _create_mock_session_with_kernels(SessionId(uuid4()), "sg2"),
    )


@pytest.fixture
def session_for_empty_scaling_group_skip() -> MagicMock:
    """Single session for testing that empty scaling groups are skipped."""
    return _create_mock_session_with_kernels(SessionId(uuid4()), "sg2")


@pytest.fixture
def session_for_termination_handler() -> MagicMock:
    """Session in TERMINATING status for handler tests."""
    return _create_mock_session_with_kernels(
        SessionId(uuid4()), "default", SessionStatus.TERMINATING
    )


@pytest.fixture
def basic_session_workload() -> SessionWorkload:
    """Basic SessionWorkload instance with default values."""
    return SessionWorkload(
        session_id=SessionId(uuid4()),
        access_key=AccessKey("test-key"),
        requested_slots=ResourceSlot({"cpu": Decimal(1), "mem": Decimal(1)}),
        user_uuid=uuid4(),
        group_id=uuid4(),
        domain_name="default",
        scaling_group="default",
        priority=0,
        session_type=SessionTypes.INTERACTIVE,
        cluster_mode=ClusterMode.SINGLE_NODE,
        starts_at=None,
        is_private=False,
        kernels=[],
        designated_agent_ids=None,
        kernel_counts_at_endpoint=None,
    )


@pytest.fixture
def batch_session_workload() -> SessionWorkload:
    """Batch SessionWorkload instance."""
    return SessionWorkload(
        session_id=SessionId(uuid4()),
        access_key=AccessKey("test-key"),
        requested_slots=ResourceSlot({"cpu": Decimal(1), "mem": Decimal(1)}),
        user_uuid=uuid4(),
        group_id=uuid4(),
        domain_name="default",
        scaling_group="default",
        priority=0,
        session_type=SessionTypes.BATCH,
        cluster_mode=ClusterMode.SINGLE_NODE,
        starts_at=None,
        is_private=False,
        kernels=[],
        designated_agent_ids=None,
        kernel_counts_at_endpoint=None,
    )


@pytest.fixture
def inference_session_workload() -> SessionWorkload:
    """Inference SessionWorkload instance."""
    return SessionWorkload(
        session_id=SessionId(uuid4()),
        access_key=AccessKey("test-key"),
        requested_slots=ResourceSlot({"cpu": Decimal(1), "mem": Decimal(1)}),
        user_uuid=uuid4(),
        group_id=uuid4(),
        domain_name="default",
        scaling_group="default",
        priority=0,
        session_type=SessionTypes.INFERENCE,
        cluster_mode=ClusterMode.SINGLE_NODE,
        starts_at=None,
        is_private=False,
        kernels=[],
        designated_agent_ids=None,
        kernel_counts_at_endpoint=None,
    )


@pytest.fixture
def minimal_resource_workload() -> SessionWorkload:
    """SessionWorkload with minimal resource requirements (1 CPU, 1 mem)."""
    return SessionWorkload(
        session_id=SessionId(uuid4()),
        access_key=AccessKey("user1"),
        requested_slots=ResourceSlot({"cpu": Decimal(1), "mem": Decimal(1)}),
        user_uuid=uuid4(),
        group_id=uuid4(),
        domain_name="default",
        scaling_group="default",
        priority=0,
        session_type=SessionTypes.INTERACTIVE,
        cluster_mode=ClusterMode.SINGLE_NODE,
        starts_at=None,
        is_private=False,
        kernels=[],
        designated_agent_ids=None,
        kernel_counts_at_endpoint=None,
    )


@pytest.fixture
def small_resource_workload() -> SessionWorkload:
    """SessionWorkload with small resource requirements."""
    return SessionWorkload(
        session_id=SessionId(uuid4()),
        access_key=AccessKey("user1"),
        requested_slots=ResourceSlot({"cpu": Decimal(2), "mem": Decimal(2)}),
        user_uuid=uuid4(),
        group_id=uuid4(),
        domain_name="default",
        scaling_group="default",
        priority=0,
        session_type=SessionTypes.INTERACTIVE,
        cluster_mode=ClusterMode.SINGLE_NODE,
        starts_at=None,
        is_private=False,
        kernels=[],
        designated_agent_ids=None,
        kernel_counts_at_endpoint=None,
    )


@pytest.fixture
def medium_resource_workload() -> SessionWorkload:
    """SessionWorkload with medium resource requirements."""
    return SessionWorkload(
        session_id=SessionId(uuid4()),
        access_key=AccessKey("user1"),
        requested_slots=ResourceSlot({"cpu": Decimal(5), "mem": Decimal(5)}),
        user_uuid=uuid4(),
        group_id=uuid4(),
        domain_name="default",
        scaling_group="default",
        priority=0,
        session_type=SessionTypes.INTERACTIVE,
        cluster_mode=ClusterMode.SINGLE_NODE,
        starts_at=None,
        is_private=False,
        kernels=[],
        designated_agent_ids=None,
        kernel_counts_at_endpoint=None,
    )


@pytest.fixture
def large_resource_workload() -> SessionWorkload:
    """SessionWorkload with large resource requirements."""
    return SessionWorkload(
        session_id=SessionId(uuid4()),
        access_key=AccessKey("user1"),
        requested_slots=ResourceSlot({"cpu": Decimal(100), "mem": Decimal(100)}),
        user_uuid=uuid4(),
        group_id=uuid4(),
        domain_name="default",
        scaling_group="default",
        priority=0,
        session_type=SessionTypes.INTERACTIVE,
        cluster_mode=ClusterMode.SINGLE_NODE,
        starts_at=None,
        is_private=False,
        kernels=[],
        designated_agent_ids=None,
        kernel_counts_at_endpoint=None,
    )


@pytest.fixture
def test_domain_name() -> str:
    """Test domain name for use in tests."""
    return "test-domain"


@pytest.fixture
def test_domain_small_resource_workload(test_domain_name: str) -> SessionWorkload:
    """SessionWorkload with small resources for domain testing."""
    return SessionWorkload(
        session_id=SessionId(uuid4()),
        access_key=AccessKey("user1"),
        requested_slots=ResourceSlot({"cpu": Decimal(2), "mem": Decimal(2)}),
        user_uuid=uuid4(),
        group_id=uuid4(),
        domain_name=test_domain_name,
        scaling_group="default",
        priority=0,
        session_type=SessionTypes.INTERACTIVE,
        cluster_mode=ClusterMode.SINGLE_NODE,
        starts_at=None,
        is_private=False,
        kernels=[],
        designated_agent_ids=None,
        kernel_counts_at_endpoint=None,
    )


@pytest.fixture
def test_domain_medium_resource_workload(test_domain_name: str) -> SessionWorkload:
    """SessionWorkload with medium resources for domain testing."""
    return SessionWorkload(
        session_id=SessionId(uuid4()),
        access_key=AccessKey("user1"),
        requested_slots=ResourceSlot({"cpu": Decimal(5), "mem": Decimal(5)}),
        user_uuid=uuid4(),
        group_id=uuid4(),
        domain_name=test_domain_name,
        scaling_group="default",
        priority=0,
        session_type=SessionTypes.INTERACTIVE,
        cluster_mode=ClusterMode.SINGLE_NODE,
        starts_at=None,
        is_private=False,
        kernels=[],
        designated_agent_ids=None,
        kernel_counts_at_endpoint=None,
    )


@pytest.fixture
def test_domain_large_resource_workload(test_domain_name: str) -> SessionWorkload:
    """SessionWorkload with large resources for domain testing."""
    return SessionWorkload(
        session_id=SessionId(uuid4()),
        access_key=AccessKey("user1"),
        requested_slots=ResourceSlot({"cpu": Decimal(100), "mem": Decimal(100)}),
        user_uuid=uuid4(),
        group_id=uuid4(),
        domain_name=test_domain_name,
        scaling_group="default",
        priority=0,
        session_type=SessionTypes.INTERACTIVE,
        cluster_mode=ClusterMode.SINGLE_NODE,
        starts_at=None,
        is_private=False,
        kernels=[],
        designated_agent_ids=None,
        kernel_counts_at_endpoint=None,
    )


@pytest.fixture
def user1_minimal_workload() -> SessionWorkload:
    """Minimal workload for user1."""
    return SessionWorkload(
        session_id=SessionId(uuid4()),
        access_key=AccessKey("user1"),
        requested_slots=ResourceSlot({"cpu": Decimal(1), "mem": Decimal(1)}),
        user_uuid=uuid4(),
        group_id=uuid4(),
        domain_name="default",
        scaling_group="default",
        priority=0,
        session_type=SessionTypes.INTERACTIVE,
        cluster_mode=ClusterMode.SINGLE_NODE,
        starts_at=None,
        is_private=False,
        kernels=[],
        designated_agent_ids=None,
        kernel_counts_at_endpoint=None,
    )


@pytest.fixture
def test_user_id() -> uuid.UUID:
    """Test user ID for use in tests."""
    return uuid4()


@pytest.fixture
def user_specific_small_workload(test_user_id: uuid.UUID) -> SessionWorkload:
    """Small workload for a specific user."""
    return SessionWorkload(
        session_id=SessionId(uuid4()),
        access_key=AccessKey("user1"),
        requested_slots=ResourceSlot({"cpu": Decimal(2), "mem": Decimal(2)}),
        user_uuid=test_user_id,
        group_id=uuid4(),
        domain_name="default",
        scaling_group="default",
        priority=0,
        session_type=SessionTypes.INTERACTIVE,
        cluster_mode=ClusterMode.SINGLE_NODE,
        starts_at=None,
        is_private=False,
        kernels=[],
        designated_agent_ids=None,
        kernel_counts_at_endpoint=None,
    )


@pytest.fixture
def user_specific_medium_workload(test_user_id: uuid.UUID) -> SessionWorkload:
    """Medium workload for a specific user."""
    return SessionWorkload(
        session_id=SessionId(uuid4()),
        access_key=AccessKey("user1"),
        requested_slots=ResourceSlot({"cpu": Decimal(5), "mem": Decimal(5)}),
        user_uuid=test_user_id,
        group_id=uuid4(),
        domain_name="default",
        scaling_group="default",
        priority=0,
        session_type=SessionTypes.INTERACTIVE,
        cluster_mode=ClusterMode.SINGLE_NODE,
        starts_at=None,
        is_private=False,
        kernels=[],
        designated_agent_ids=None,
        kernel_counts_at_endpoint=None,
    )


@pytest.fixture
def user_specific_minimal_workload(test_user_id: uuid.UUID) -> SessionWorkload:
    """Minimal workload for a specific user."""
    return SessionWorkload(
        session_id=SessionId(uuid4()),
        access_key=AccessKey("user1"),
        requested_slots=ResourceSlot({"cpu": Decimal(1), "mem": Decimal(1)}),
        user_uuid=test_user_id,
        group_id=uuid4(),
        domain_name="default",
        scaling_group="default",
        priority=0,
        session_type=SessionTypes.INTERACTIVE,
        cluster_mode=ClusterMode.SINGLE_NODE,
        starts_at=None,
        is_private=False,
        kernels=[],
        designated_agent_ids=None,
        kernel_counts_at_endpoint=None,
    )


@pytest.fixture
def batch_session_past_start_time() -> SessionWorkload:
    """Batch session with start time in the past."""
    past_time = datetime.now(tzutc()) - timedelta(hours=1)
    return SessionWorkload(
        session_id=SessionId(uuid4()),
        access_key=AccessKey("test-key"),
        requested_slots=ResourceSlot({"cpu": Decimal(1), "mem": Decimal(1)}),
        user_uuid=uuid4(),
        group_id=uuid4(),
        domain_name="default",
        scaling_group="default",
        priority=0,
        session_type=SessionTypes.BATCH,
        cluster_mode=ClusterMode.SINGLE_NODE,
        starts_at=past_time,
        is_private=False,
        kernels=[],
        designated_agent_ids=None,
        kernel_counts_at_endpoint=None,
    )


@pytest.fixture
def batch_session_future_start_time() -> SessionWorkload:
    """Batch session with start time in the future."""
    future_time = datetime.now(tzutc()) + timedelta(hours=1)
    return SessionWorkload(
        session_id=SessionId(uuid4()),
        access_key=AccessKey("test-key"),
        requested_slots=ResourceSlot({"cpu": Decimal(1), "mem": Decimal(1)}),
        user_uuid=uuid4(),
        group_id=uuid4(),
        domain_name="default",
        scaling_group="default",
        priority=0,
        session_type=SessionTypes.BATCH,
        cluster_mode=ClusterMode.SINGLE_NODE,
        starts_at=future_time,
        is_private=False,
        kernels=[],
        designated_agent_ids=None,
        kernel_counts_at_endpoint=None,
    )


# =============================================================================
# Coordinator Test Fixtures
# =============================================================================


@pytest.fixture
def session_transition_info_pending() -> SessionTransitionInfo:
    """SessionTransitionInfo for PENDING session."""
    return SessionTransitionInfo(
        session_id=SessionId(uuid4()),
        from_status=SessionStatus.PENDING,
        reason="test-reason",
        creation_id=str(uuid4()),
        access_key=AccessKey("test-key"),
    )


@pytest.fixture
def session_transition_info_preparing() -> SessionTransitionInfo:
    """SessionTransitionInfo for PREPARING session."""
    return SessionTransitionInfo(
        session_id=SessionId(uuid4()),
        from_status=SessionStatus.PREPARING,
        reason="test-reason",
        creation_id=str(uuid4()),
        access_key=AccessKey("test-key"),
    )


@pytest.fixture
def failure_sessions_for_classification() -> list[SessionTransitionInfo]:
    """Multiple failure sessions for classification tests."""
    return [
        SessionTransitionInfo(
            session_id=SessionId(uuid4()),
            from_status=SessionStatus.PREPARING,
            reason="failure-1",
            creation_id=str(uuid4()),
            access_key=AccessKey("test-key"),
        ),
        SessionTransitionInfo(
            session_id=SessionId(uuid4()),
            from_status=SessionStatus.PREPARING,
            reason="failure-2",
            creation_id=str(uuid4()),
            access_key=AccessKey("test-key"),
        ),
        SessionTransitionInfo(
            session_id=SessionId(uuid4()),
            from_status=SessionStatus.PREPARING,
            reason="failure-3",
            creation_id=str(uuid4()),
            access_key=AccessKey("test-key"),
        ),
    ]


@pytest.fixture
def session_execution_result_success() -> SessionExecutionResult:
    """SessionExecutionResult with successful sessions."""
    return SessionExecutionResult(
        successes=[
            SessionTransitionInfo(
                session_id=SessionId(uuid4()),
                from_status=SessionStatus.PREPARING,
                reason="scheduled",
                creation_id=str(uuid4()),
                access_key=AccessKey("test-key"),
            ),
        ],
        failures=[],
        skipped=[],
    )


@pytest.fixture
def session_execution_result_with_failures() -> SessionExecutionResult:
    """SessionExecutionResult with failures."""
    return SessionExecutionResult(
        successes=[
            SessionTransitionInfo(
                session_id=SessionId(uuid4()),
                from_status=SessionStatus.PREPARING,
                reason="scheduled",
                creation_id=str(uuid4()),
                access_key=AccessKey("test-key"),
            ),
        ],
        failures=[
            SessionTransitionInfo(
                session_id=SessionId(uuid4()),
                from_status=SessionStatus.PREPARING,
                reason="failed",
                creation_id=str(uuid4()),
                access_key=AccessKey("test-key"),
            ),
        ],
        skipped=[],
    )


@pytest.fixture
def session_execution_result_with_skipped() -> SessionExecutionResult:
    """SessionExecutionResult with skipped sessions."""
    return SessionExecutionResult(
        successes=[],
        failures=[],
        skipped=[
            SessionTransitionInfo(
                session_id=SessionId(uuid4()),
                from_status=SessionStatus.PENDING,
                reason="skipped-due-to-priority",
                creation_id=str(uuid4()),
                access_key=AccessKey("test-key"),
            ),
        ],
    )


@pytest.fixture
def session_execution_result_empty() -> SessionExecutionResult:
    """Empty SessionExecutionResult."""
    return SessionExecutionResult(
        successes=[],
        failures=[],
        skipped=[],
    )


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


@pytest.fixture
def empty_system_snapshot() -> SystemSnapshot:
    """Create an empty system snapshot for testing."""
    return SystemSnapshot(
        total_capacity=ResourceSlot({"cpu": Decimal("100"), "mem": Decimal("100")}),
        resource_occupancy=ResourceOccupancySnapshot(
            by_keypair={}, by_user={}, by_group={}, by_domain={}, by_agent={}
        ),
        resource_policy=ResourcePolicySnapshot(
            keypair_policies={},
            user_policies={},
            group_limits={},
            domain_limits={},
        ),
        concurrency=ConcurrencySnapshot(
            sessions_by_keypair={},
            sftp_sessions_by_keypair={},
        ),
        pending_sessions=PendingSessionSnapshot(
            by_keypair={},
        ),
        session_dependencies=SessionDependencySnapshot(
            by_session={},
        ),
        known_slot_types={},
    )
