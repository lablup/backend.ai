from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Final
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from ai.backend.common.exception import ErrorCode
from ai.backend.manager.actions.action import (
    BaseAction,
    BaseActionResult,
    BaseActionResultMeta,
    BaseActionTriggerMeta,
    ProcessResult,
)
from ai.backend.manager.actions.monitors.audit_log import AuditLogMonitor
from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.processor.base import ActionProcessorFactory
from ai.backend.manager.actions.types import OperationStatus

_MOCK_ACTION_TYPE: Final[str] = "test"
_MOCK_OPERATION_TYPE: Final[str] = "create"


@dataclass
class MockAction(BaseAction):
    id: str
    type: str
    operation: str

    def entity_id(self) -> str | None:
        return self.id

    @classmethod
    def entity_type(cls) -> str:
        return _MOCK_ACTION_TYPE

    @classmethod
    def operation_type(cls) -> str:
        return _MOCK_OPERATION_TYPE


@dataclass
class MockActionResult(BaseActionResult):
    id: str

    def entity_id(self) -> str | None:
        return self.id


class MockActionTriggerMeta:
    pass


class MockException(Exception):
    pass


class MockActionMonitor(ActionMonitor):
    expected_prepare_action: MockAction
    expected_done_action: MockAction
    expected_done_result: ProcessResult

    def __init__(
        self,
        expected_prepare_action: MockAction,
        expected_done_action: MockAction,
        expected_done_result: ProcessResult,
    ):
        self.expected_prepare_action = expected_prepare_action
        self.expected_done_action = expected_done_action
        self.expected_done_result = expected_done_result

    async def prepare(self, action: BaseAction, meta: BaseActionTriggerMeta) -> None:
        assert isinstance(action, MockAction)
        assert action == self.expected_prepare_action

    async def done(self, action: BaseAction, result: ProcessResult) -> None:
        assert isinstance(action, MockAction)
        assert action == self.expected_done_action
        # Partially check the result
        assert result.meta.status == self.expected_done_result.meta.status
        assert result.meta.description == self.expected_done_result.meta.description
        current_time = datetime.now(tz=UTC)
        assert result.meta.started_at < current_time
        assert result.meta.started_at <= result.meta.ended_at
        assert result.meta.ended_at < current_time
        assert result.meta.entity_id == self.expected_done_result.meta.entity_id
        assert result.meta.duration.total_seconds() >= 0


async def mock_action_processor_func(action: MockAction) -> MockActionResult:
    return MockActionResult(id=action.id)


async def mock_exception_processor_func(action: MockAction) -> MockActionResult:
    raise MockException("Mock exception")


async def test_processor_success() -> None:
    now = datetime.now(tz=UTC)
    monitor = MockActionMonitor(
        expected_prepare_action=MockAction(
            id="1", type=_MOCK_ACTION_TYPE, operation=_MOCK_OPERATION_TYPE
        ),
        expected_done_action=MockAction(
            id="1", type=_MOCK_ACTION_TYPE, operation=_MOCK_OPERATION_TYPE
        ),
        expected_done_result=ProcessResult(
            meta=BaseActionResultMeta(
                action_id=uuid4(),
                entity_id="1",
                status=OperationStatus.SUCCESS,
                description="Success",
                started_at=now,
                ended_at=now,
                duration=timedelta(seconds=0.0),
                error_code=None,
            ),
        ),
    )
    processor = ActionProcessor[MockAction, MockActionResult](
        func=mock_action_processor_func, monitors=[monitor]
    )
    action = MockAction(id="1", type=_MOCK_ACTION_TYPE, operation=_MOCK_OPERATION_TYPE)
    result = await processor.wait_for_complete(action)

    assert result.entity_id() == "1"


async def test_processor_exception() -> None:
    now = datetime.now(tz=UTC)
    monitor = MockActionMonitor(
        expected_prepare_action=MockAction(
            id="1", type=_MOCK_ACTION_TYPE, operation=_MOCK_OPERATION_TYPE
        ),
        expected_done_action=MockAction(
            id="1", type=_MOCK_ACTION_TYPE, operation=_MOCK_OPERATION_TYPE
        ),
        expected_done_result=ProcessResult(
            meta=BaseActionResultMeta(
                action_id=uuid4(),
                entity_id="1",
                status=OperationStatus.ERROR,
                description="Mock exception",
                started_at=now,
                ended_at=now,
                duration=timedelta(seconds=0.0),
                error_code=ErrorCode.default(),
            ),
        ),
    )
    processor = ActionProcessor[MockAction, MockActionResult](
        func=mock_exception_processor_func, monitors=[monitor]
    )
    action = MockAction(id="1", type=_MOCK_ACTION_TYPE, operation=_MOCK_OPERATION_TYPE)

    with pytest.raises(MockException):
        await processor.wait_for_complete(action)


class TrackingMonitor(ActionMonitor):
    """Monitor that tracks whether its methods were called."""

    def __init__(self) -> None:
        self.prepare_called = False
        self.done_called = False

    async def prepare(self, action: BaseAction, meta: BaseActionTriggerMeta) -> None:
        self.prepare_called = True

    async def done(self, action: BaseAction, result: ProcessResult) -> None:
        self.done_called = True


class AnotherTrackingMonitor(ActionMonitor):
    """Another monitor type for testing exclusion by type."""

    def __init__(self) -> None:
        self.prepare_called = False
        self.done_called = False

    async def prepare(self, action: BaseAction, meta: BaseActionTriggerMeta) -> None:
        self.prepare_called = True

    async def done(self, action: BaseAction, result: ProcessResult) -> None:
        self.done_called = True


class TestActionProcessorFactory:
    """Tests for ActionProcessorFactory monitor/validator exclusion at setup time."""

    @pytest.fixture
    def tracking_monitor(self) -> TrackingMonitor:
        return TrackingMonitor()

    @pytest.fixture
    def another_tracking_monitor(self) -> AnotherTrackingMonitor:
        return AnotherTrackingMonitor()

    @pytest.fixture
    def mock_action(self) -> MockAction:
        return MockAction(id="1", type=_MOCK_ACTION_TYPE, operation=_MOCK_OPERATION_TYPE)

    @pytest.mark.asyncio
    async def test_factory_includes_all_monitors_when_no_exclusions(
        self,
        tracking_monitor: TrackingMonitor,
        another_tracking_monitor: AnotherTrackingMonitor,
        mock_action: MockAction,
    ) -> None:
        """Factory should include all monitors when no exclusions are specified."""
        factory = ActionProcessorFactory(
            monitors=[tracking_monitor, another_tracking_monitor],
        )
        processor = factory.build_action_processor(mock_action_processor_func)

        await processor.wait_for_complete(mock_action)

        assert tracking_monitor.prepare_called is True
        assert tracking_monitor.done_called is True
        assert another_tracking_monitor.prepare_called is True
        assert another_tracking_monitor.done_called is True

    @pytest.mark.asyncio
    async def test_factory_excludes_monitors_by_default_exclusion(
        self,
        tracking_monitor: TrackingMonitor,
        another_tracking_monitor: AnotherTrackingMonitor,
        mock_action: MockAction,
    ) -> None:
        """Factory should exclude monitors specified in default_excluded_monitors."""
        factory = ActionProcessorFactory(
            monitors=[tracking_monitor, another_tracking_monitor],
            default_excluded_monitors={TrackingMonitor},
        )
        processor = factory.build_action_processor(mock_action_processor_func)

        await processor.wait_for_complete(mock_action)

        # TrackingMonitor should be excluded
        assert tracking_monitor.prepare_called is False
        assert tracking_monitor.done_called is False
        # AnotherTrackingMonitor should still be called
        assert another_tracking_monitor.prepare_called is True
        assert another_tracking_monitor.done_called is True

    @pytest.mark.asyncio
    async def test_factory_excludes_monitors_by_additional_exclusion(
        self,
        tracking_monitor: TrackingMonitor,
        another_tracking_monitor: AnotherTrackingMonitor,
        mock_action: MockAction,
    ) -> None:
        """Factory should exclude monitors specified in additional_excluded_monitors."""
        factory = ActionProcessorFactory(
            monitors=[tracking_monitor, another_tracking_monitor],
        )
        processor = factory.build_action_processor(
            mock_action_processor_func,
            additional_excluded_monitors={AnotherTrackingMonitor},
        )

        await processor.wait_for_complete(mock_action)

        # TrackingMonitor should still be called
        assert tracking_monitor.prepare_called is True
        assert tracking_monitor.done_called is True
        # AnotherTrackingMonitor should be excluded
        assert another_tracking_monitor.prepare_called is False
        assert another_tracking_monitor.done_called is False

    @pytest.mark.asyncio
    async def test_factory_combines_default_and_additional_exclusions(
        self,
        mock_action: MockAction,
    ) -> None:
        """Factory should combine default and additional exclusions."""
        monitor1 = TrackingMonitor()
        monitor2 = AnotherTrackingMonitor()

        factory = ActionProcessorFactory(
            monitors=[monitor1, monitor2],
            default_excluded_monitors={TrackingMonitor},
        )
        processor = factory.build_action_processor(
            mock_action_processor_func,
            additional_excluded_monitors={AnotherTrackingMonitor},
        )

        await processor.wait_for_complete(mock_action)

        # Both monitors should be excluded
        assert monitor1.prepare_called is False
        assert monitor1.done_called is False
        assert monitor2.prepare_called is False
        assert monitor2.done_called is False

    @pytest.mark.asyncio
    async def test_factory_default_exclusion_applies_to_all_processors(
        self,
        mock_action: MockAction,
    ) -> None:
        """Default exclusions should apply to all processors built by the factory."""
        monitor1 = TrackingMonitor()
        monitor2 = AnotherTrackingMonitor()

        factory = ActionProcessorFactory(
            monitors=[monitor1, monitor2],
            default_excluded_monitors={TrackingMonitor},
        )

        # Build two different processors
        processor1 = factory.build_action_processor(mock_action_processor_func)
        processor2 = factory.build_action_processor(mock_action_processor_func)

        await processor1.wait_for_complete(mock_action)

        # TrackingMonitor excluded from processor1
        assert monitor1.prepare_called is False

        # Reset for processor2
        monitor1.prepare_called = False
        monitor2.prepare_called = False

        await processor2.wait_for_complete(mock_action)

        # TrackingMonitor still excluded from processor2
        assert monitor1.prepare_called is False
        assert monitor2.prepare_called is True


class TestAuditLogMonitorExclusionAtSetupTime:
    """Test that AuditLogMonitor can be excluded at processor setup time.

    This verifies the design where high-frequency actions like heartbeat
    have AuditLogMonitor excluded at ActionProcessorFactory.build_action_processor()
    rather than runtime filtering inside AuditLogMonitor.
    """

    @pytest.fixture
    def mock_audit_log_repository(self) -> MagicMock:
        """Mock AuditLogRepository to track create() calls."""
        repo = MagicMock()
        repo.create = MagicMock(return_value=None)
        return repo

    @pytest.fixture
    def audit_log_monitor(self, mock_audit_log_repository: MagicMock) -> AuditLogMonitor:
        """Real AuditLogMonitor with mocked repository."""
        return AuditLogMonitor(repository=mock_audit_log_repository)

    @pytest.fixture
    def mock_action(self) -> MockAction:
        return MockAction(id="1", type=_MOCK_ACTION_TYPE, operation=_MOCK_OPERATION_TYPE)

    @pytest.mark.asyncio
    async def test_audit_log_monitor_excluded_via_factory(
        self,
        audit_log_monitor: AuditLogMonitor,
        mock_audit_log_repository: MagicMock,
        mock_action: MockAction,
    ) -> None:
        """AuditLogMonitor should not be called when excluded via factory."""
        factory = ActionProcessorFactory(
            monitors=[audit_log_monitor],
        )

        # Build processor with AuditLogMonitor excluded (simulating heartbeat processor)
        processor = factory.build_action_processor(
            mock_action_processor_func,
            additional_excluded_monitors={AuditLogMonitor},
        )

        await processor.wait_for_complete(mock_action)

        # Verify that repository.create() was NOT called
        mock_audit_log_repository.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_audit_log_monitor_included_when_not_excluded(
        self,
        audit_log_monitor: AuditLogMonitor,
        mock_audit_log_repository: MagicMock,
        mock_action: MockAction,
    ) -> None:
        """AuditLogMonitor should be called when not excluded."""
        factory = ActionProcessorFactory(
            monitors=[audit_log_monitor],
        )

        # Build processor without excluding AuditLogMonitor
        processor = factory.build_action_processor(mock_action_processor_func)

        await processor.wait_for_complete(mock_action)

        # Verify that repository.create() WAS called
        mock_audit_log_repository.create.assert_called_once()
