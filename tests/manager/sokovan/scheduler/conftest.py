"""Common fixtures for sokovan scheduler tests."""

import uuid
from decimal import Decimal
from uuid import uuid4

import pytest

from ai.backend.common.types import (
    AccessKey,
    ClusterMode,
    ResourceSlot,
    SessionId,
    SessionTypes,
)
from ai.backend.manager.sokovan.scheduler.types import (
    ConcurrencySnapshot,
    PendingSessionSnapshot,
    ResourceOccupancySnapshot,
    ResourcePolicySnapshot,
    SessionDependencySnapshot,
    SessionWorkload,
    SystemSnapshot,
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
    from datetime import datetime, timedelta

    from dateutil.tz import tzutc

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
    from datetime import datetime, timedelta

    from dateutil.tz import tzutc

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
