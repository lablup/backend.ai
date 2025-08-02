from datetime import datetime, timedelta
from uuid import uuid4

import pytest
from dateutil.tz import tzutc

from ai.backend.common.types import AccessKey, ResourceSlot, SessionId, SessionTypes
from ai.backend.manager.sokovan.scheduler.types import (
    ConcurrencySnapshot,
    PendingSessionSnapshot,
    ResourceOccupancySnapshot,
    ResourcePolicySnapshot,
    SessionDependencySnapshot,
    SessionWorkload,
    SystemSnapshot,
)
from ai.backend.manager.sokovan.scheduler.validators.exceptions import SchedulingValidationError
from ai.backend.manager.sokovan.scheduler.validators.reserved_batch import (
    ReservedBatchSessionValidator,
)


def create_empty_snapshot() -> SystemSnapshot:
    """Create an empty system snapshot for testing."""
    return SystemSnapshot(
        total_capacity=ResourceSlot({"cpu": 100, "memory": 1024}),
        resource_occupancy=ResourceOccupancySnapshot({}, {}, {}, {}),
        resource_policy=ResourcePolicySnapshot({}, {}, {}, {}),
        concurrency=ConcurrencySnapshot({}, {}),
        pending_sessions=PendingSessionSnapshot({}),
        session_dependencies=SessionDependencySnapshot({}),
    )


class TestReservedBatchSessionValidator:
    def test_non_batch_session_passes(self) -> None:
        """Non-batch sessions should always pass validation."""
        validator = ReservedBatchSessionValidator()
        snapshot = create_empty_snapshot()

        # Interactive session
        workload = SessionWorkload(
            session_id=SessionId(uuid4()),
            access_key=AccessKey("test-key"),
            requested_slots=ResourceSlot({"cpu": 1, "memory": 1}),
            user_uuid=uuid4(),
            group_id=uuid4(),
            domain_name="default",
            session_type=SessionTypes.INTERACTIVE,
        )

        # Should not raise
        validator.validate(snapshot, workload)

    def test_batch_session_without_start_time_passes(self) -> None:
        """Batch sessions without a scheduled start time should pass."""
        validator = ReservedBatchSessionValidator()
        snapshot = create_empty_snapshot()

        workload = SessionWorkload(
            session_id=SessionId(uuid4()),
            access_key=AccessKey("test-key"),
            requested_slots=ResourceSlot({"cpu": 1, "memory": 1}),
            user_uuid=uuid4(),
            group_id=uuid4(),
            domain_name="default",
            session_type=SessionTypes.BATCH,
            starts_at=None,
        )

        # Should not raise
        validator.validate(snapshot, workload)

    def test_batch_session_after_start_time_passes(self) -> None:
        """Batch sessions after their scheduled start time should pass."""
        validator = ReservedBatchSessionValidator()
        snapshot = create_empty_snapshot()

        # Set start time to 1 hour ago
        past_time = datetime.now(tzutc()) - timedelta(hours=1)
        workload = SessionWorkload(
            session_id=SessionId(uuid4()),
            access_key=AccessKey("test-key"),
            requested_slots=ResourceSlot({"cpu": 1, "memory": 1}),
            user_uuid=uuid4(),
            group_id=uuid4(),
            domain_name="default",
            session_type=SessionTypes.BATCH,
            starts_at=past_time,
        )

        # Should not raise
        validator.validate(snapshot, workload)

    def test_batch_session_before_start_time_fails(self) -> None:
        """Batch sessions before their scheduled start time should fail."""
        validator = ReservedBatchSessionValidator()
        snapshot = create_empty_snapshot()

        # Set start time to 1 hour in the future
        future_time = datetime.now(tzutc()) + timedelta(hours=1)
        workload = SessionWorkload(
            session_id=SessionId(uuid4()),
            access_key=AccessKey("test-key"),
            requested_slots=ResourceSlot({"cpu": 1, "memory": 1}),
            user_uuid=uuid4(),
            group_id=uuid4(),
            domain_name="default",
            session_type=SessionTypes.BATCH,
            starts_at=future_time,
        )

        with pytest.raises(SchedulingValidationError, match="Before start time"):
            validator.validate(snapshot, workload)
