import pytest

from ai.backend.common.types import ResourceSlot
from ai.backend.manager.sokovan.scheduler.provisioner.validators.exceptions import (
    SchedulingValidationError,
)
from ai.backend.manager.sokovan.scheduler.provisioner.validators.reserved_batch import (
    ReservedBatchSessionValidator,
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


def create_empty_snapshot() -> SystemSnapshot:
    """Create an empty system snapshot for testing."""
    return SystemSnapshot(
        total_capacity=ResourceSlot({"cpu": 100, "memory": 1024}),
        resource_occupancy=ResourceOccupancySnapshot(
            by_keypair={}, by_user={}, by_group={}, by_domain={}, by_agent={}
        ),
        resource_policy=ResourcePolicySnapshot({}, {}, {}, {}),
        concurrency=ConcurrencySnapshot({}, {}),
        pending_sessions=PendingSessionSnapshot({}),
        session_dependencies=SessionDependencySnapshot({}),
        known_slot_types={},
    )


class TestReservedBatchSessionValidator:
    def test_non_batch_session_passes(self, basic_session_workload: SessionWorkload) -> None:
        """Non-batch sessions should always pass validation."""
        validator = ReservedBatchSessionValidator()
        snapshot = create_empty_snapshot()

        # Interactive session (basic_session_workload is already INTERACTIVE)
        workload = basic_session_workload

        # Should not raise
        validator.validate(snapshot, workload)

    def test_batch_session_without_start_time_passes(
        self, batch_session_workload: SessionWorkload
    ) -> None:
        """Batch sessions without a scheduled start time should pass."""
        validator = ReservedBatchSessionValidator()
        snapshot = create_empty_snapshot()

        # batch_session_workload already has starts_at=None
        workload = batch_session_workload

        # Should not raise
        validator.validate(snapshot, workload)

    def test_batch_session_after_start_time_passes(
        self, batch_session_past_start_time: SessionWorkload
    ) -> None:
        """Batch sessions after their scheduled start time should pass."""
        validator = ReservedBatchSessionValidator()
        snapshot = create_empty_snapshot()

        workload = batch_session_past_start_time

        # Should not raise
        validator.validate(snapshot, workload)

    def test_batch_session_before_start_time_fails(
        self, batch_session_future_start_time: SessionWorkload
    ) -> None:
        """Batch sessions before their scheduled start time should fail."""
        validator = ReservedBatchSessionValidator()
        snapshot = create_empty_snapshot()

        workload = batch_session_future_start_time

        with pytest.raises(SchedulingValidationError, match="Before start time"):
            validator.validate(snapshot, workload)
