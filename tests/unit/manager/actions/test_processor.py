from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Final, Optional

import pytest

from ai.backend.common.exception import ErrorCode
from ai.backend.manager.actions.action import (
    BaseAction,
    BaseActionResult,
    BaseActionResultMeta,
    BaseActionTriggerMeta,
    ProcessResult,
)
from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import ActionSpec

_MOCK_ACTION_TYPE: Final[str] = "test"
_MOCK_OPERATION_TYPE: Final[str] = "create"


@dataclass
class MockAction(BaseAction):
    id: str
    type: str
    operation: str

    def entity_id(self) -> Optional[str]:
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

    def entity_id(self) -> Optional[str]:
        return self.id


class MockActionTriggerMeta:
    pass


class MockException(Exception):
    pass


class MockActionMonitor:
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

    async def prepare(self, action: MockAction, _meta: MockActionTriggerMeta) -> None:
        assert action == self.expected_prepare_action

    async def done(self, action: MockAction, result: ProcessResult) -> None:
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


async def test_processor_success():
    monitor = MockActionMonitor(
        expected_prepare_action=MockAction(
            id="1", type=_MOCK_ACTION_TYPE, operation=_MOCK_OPERATION_TYPE
        ),
        expected_done_action=MockAction(
            id="1", type=_MOCK_ACTION_TYPE, operation=_MOCK_OPERATION_TYPE
        ),
        expected_done_result=ProcessResult(
            meta=BaseActionResultMeta(
                action_id=None,
                entity_id="1",
                status="success",
                description="Success",
                started_at=None,
                ended_at=None,
                duration=0.0,
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


async def test_processor_exception():
    monitor = MockActionMonitor(
        expected_prepare_action=MockAction(
            id="1", type=_MOCK_ACTION_TYPE, operation=_MOCK_OPERATION_TYPE
        ),
        expected_done_action=MockAction(
            id="1", type=_MOCK_ACTION_TYPE, operation=_MOCK_OPERATION_TYPE
        ),
        expected_done_result=ProcessResult(
            meta=BaseActionResultMeta(
                action_id=None,
                entity_id="1",
                status="error",
                description="Mock exception",
                started_at=None,
                ended_at=None,
                duration=0.0,
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


class ExclusionAwareMonitor(ActionMonitor):
    """Monitor that respects excluded action specs, like AuditLogMonitor"""

    def __init__(self, excluded_action_specs: frozenset[ActionSpec] | None = None) -> None:
        self.prepare_called = False
        self.done_called = False
        self.log_generated = False
        self._excluded_action_specs = excluded_action_specs or frozenset()

    async def prepare(self, action: BaseAction, meta: BaseActionTriggerMeta) -> None:
        self.prepare_called = True

    async def done(self, action: BaseAction, result: ProcessResult) -> None:
        self.done_called = True
        # Check exclusion like AuditLogMonitor does
        if action.spec() not in self._excluded_action_specs:
            self.log_generated = True


@dataclass
class MockActionTypeA(BaseAction):
    """Mock action type A for testing exclusion"""

    id: str

    def entity_id(self) -> str | None:
        return self.id

    @classmethod
    def entity_type(cls) -> str:
        return "type_a"

    @classmethod
    def operation_type(cls) -> str:
        return "op_a"


@dataclass
class MockActionTypeB(BaseAction):
    """Mock action type B for testing exclusion"""

    id: str

    def entity_id(self) -> str | None:
        return self.id

    @classmethod
    def entity_type(cls) -> str:
        return "type_b"

    @classmethod
    def operation_type(cls) -> str:
        return "op_b"


@dataclass
class MockActionResultForExclusion(BaseActionResult):
    """Result for mock actions in exclusion tests"""

    id: str

    def entity_id(self) -> str | None:
        return self.id


async def mock_exclusion_action_func(action: BaseAction) -> MockActionResultForExclusion:
    """Mock function for processing actions in exclusion tests"""
    return MockActionResultForExclusion(id=action.entity_id() or "unknown")


class TestMonitorExclusionBySpec:
    """Test monitor exclusion based on action specs configured at registration time"""

    @pytest.fixture
    def action_type_a(self) -> MockActionTypeA:
        """Create an action of type A"""
        return MockActionTypeA(id="a-1")

    @pytest.fixture
    def action_type_b(self) -> MockActionTypeB:
        """Create an action of type B"""
        return MockActionTypeB(id="b-1")

    @pytest.fixture
    def monitor_excluding_type_a(self) -> ExclusionAwareMonitor:
        """Create a monitor that excludes type A actions"""
        return ExclusionAwareMonitor(excluded_action_specs=frozenset({MockActionTypeA.spec()}))

    @pytest.fixture
    def monitor_excluding_nothing(self) -> ExclusionAwareMonitor:
        """Create a monitor that excludes no actions"""
        return ExclusionAwareMonitor()

    @pytest.mark.asyncio
    async def test_monitor_skips_excluded_action_spec(
        self,
        action_type_a: MockActionTypeA,
        monitor_excluding_type_a: ExclusionAwareMonitor,
    ) -> None:
        """Monitor should skip logging for actions matching excluded specs"""
        processor = ActionProcessor(
            func=mock_exclusion_action_func,
            monitors=[monitor_excluding_type_a],
        )
        await processor.wait_for_complete(action_type_a)

        assert monitor_excluding_type_a.prepare_called is True
        assert monitor_excluding_type_a.done_called is True
        assert monitor_excluding_type_a.log_generated is False  # Skipped due to exclusion

    @pytest.mark.asyncio
    async def test_monitor_logs_non_excluded_action_spec(
        self,
        action_type_b: MockActionTypeB,
        monitor_excluding_type_a: ExclusionAwareMonitor,
    ) -> None:
        """Monitor should log actions not matching excluded specs"""
        processor = ActionProcessor(
            func=mock_exclusion_action_func,
            monitors=[monitor_excluding_type_a],
        )
        await processor.wait_for_complete(action_type_b)

        assert monitor_excluding_type_a.prepare_called is True
        assert monitor_excluding_type_a.done_called is True
        assert monitor_excluding_type_a.log_generated is True  # Logged because not excluded

    @pytest.mark.asyncio
    async def test_monitor_with_no_exclusions_logs_all(
        self,
        action_type_a: MockActionTypeA,
        action_type_b: MockActionTypeB,
        monitor_excluding_nothing: ExclusionAwareMonitor,
    ) -> None:
        """Monitor with no exclusions should log all actions"""
        processor = ActionProcessor(
            func=mock_exclusion_action_func,
            monitors=[monitor_excluding_nothing],
        )

        await processor.wait_for_complete(action_type_a)
        assert monitor_excluding_nothing.log_generated is True

        # Reset and test type B
        monitor_excluding_nothing.log_generated = False
        await processor.wait_for_complete(action_type_b)
        assert monitor_excluding_nothing.log_generated is True
