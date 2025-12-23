from dataclasses import dataclass
from datetime import datetime
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
from ai.backend.manager.actions.types import MonitorTag

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
        current_time = datetime.now()
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


class TagUnawareMonitor(ActionMonitor):
    """Monitor that tracks whether its methods were called"""

    def __init__(self) -> None:
        self.prepare_called = False
        self.done_called = False
        self.last_action: Optional[BaseAction] = None
        self.last_result: Optional[ProcessResult] = None

    async def prepare(self, action: BaseAction, meta: BaseActionTriggerMeta) -> None:
        self.prepare_called = True
        self.last_action = action

    async def done(self, action: BaseAction, result: ProcessResult) -> None:
        self.done_called = True
        self.last_action = action
        self.last_result = result


class TagAwareMonitor(ActionMonitor):
    """Monitor that respects SKIP_AUDIT_LOG tag like AuditLogMonitor"""

    def __init__(self) -> None:
        self.prepare_called = False
        self.done_called = False
        self.log_generated = False

    async def prepare(self, action: BaseAction, meta: BaseActionTriggerMeta) -> None:
        self.prepare_called = True

    async def done(self, action: BaseAction, result: ProcessResult) -> None:
        self.done_called = True
        # Check tag like AuditLogMonitor does
        if MonitorTag.SKIP_AUDIT_LOG not in action.monitor_tags():
            self.log_generated = True


@dataclass
class MockActionWithTag(BaseAction):
    """Mock action with SKIP_AUDIT_LOG tag"""

    id: str

    def entity_id(self) -> Optional[str]:
        return self.id

    @classmethod
    def entity_type(cls) -> str:
        return "test_tagged"

    @classmethod
    def operation_type(cls) -> str:
        return "test_op"

    @classmethod
    def monitor_tags(cls) -> frozenset[MonitorTag]:
        return frozenset({MonitorTag.SKIP_AUDIT_LOG})


@dataclass
class MockActionWithoutTag(BaseAction):
    """Mock action without any tags (default behavior)"""

    id: str

    def entity_id(self) -> Optional[str]:
        return self.id

    @classmethod
    def entity_type(cls) -> str:
        return "test_untagged"

    @classmethod
    def operation_type(cls) -> str:
        return "test_op"


@dataclass
class MockTaggedActionResult(BaseActionResult):
    """Result for mock tagged actions"""

    id: str

    def entity_id(self) -> Optional[str]:
        return self.id


async def mock_tagged_action_func(action: BaseAction) -> MockTaggedActionResult:
    """Mock function for processing tagged actions"""
    return MockTaggedActionResult(id=action.entity_id() or "unknown")


class TestMonitorTagFiltering:
    """Test monitor filtering based on action monitor_tags"""

    # Fixtures

    @pytest.fixture
    def tag_unaware_monitor(self) -> TagUnawareMonitor:
        """Create a tag-unaware monitor that does not respect SKIP_AUDIT_LOG tag"""
        return TagUnawareMonitor()

    @pytest.fixture
    def tag_aware_monitor(self) -> TagAwareMonitor:
        """Create a tag-aware monitor that respects SKIP_AUDIT_LOG tag"""
        return TagAwareMonitor()

    @pytest.fixture
    def tagged_action(self) -> MockActionWithTag:
        """Create an action with SKIP_AUDIT_LOG tag"""
        return MockActionWithTag(id="tagged-1")

    @pytest.fixture
    def untagged_action(self) -> MockActionWithoutTag:
        """Create an action without tags"""
        return MockActionWithoutTag(id="untagged-1")

    @pytest.fixture
    def processor_with_tag_unaware(self, tag_unaware_monitor: TagUnawareMonitor) -> ActionProcessor:
        """Create a processor with tag-unaware monitor"""
        return ActionProcessor(
            func=mock_tagged_action_func,
            monitors=[tag_unaware_monitor],
        )

    @pytest.fixture
    def processor_with_tag_aware(self, tag_aware_monitor: TagAwareMonitor) -> ActionProcessor:
        """Create a processor with tag-aware monitor"""
        return ActionProcessor(
            func=mock_tagged_action_func,
            monitors=[tag_aware_monitor],
        )

    # Tests

    @pytest.mark.asyncio
    async def test_tag_unaware_monitor_calls_done_even_with_skip_audit_tag(
        self,
        processor_with_tag_unaware: ActionProcessor,
        tagged_action: MockActionWithTag,
        tag_unaware_monitor: TagUnawareMonitor,
    ) -> None:
        """Tag-unaware monitors call both prepare() and done() even when SKIP_AUDIT_LOG tag is present.
        This test demonstrates that TagUnawareMonitor does not respect the SKIP_AUDIT_LOG tag,
        and calls done() regardless. This is why tag-aware monitors (like AuditLogMonitor)
        need to check the tag themselves in their done() method and skip logging if present.
        """
        result = await processor_with_tag_unaware.wait_for_complete(tagged_action)

        assert result.entity_id() == "tagged-1"
        assert tag_unaware_monitor.prepare_called is True
        assert tag_unaware_monitor.done_called is True
        assert tag_unaware_monitor.last_action == tagged_action

    @pytest.mark.asyncio
    async def test_action_without_tag_triggers_monitor_done(
        self,
        processor_with_tag_unaware: ActionProcessor,
        untagged_action: MockActionWithoutTag,
        tag_unaware_monitor: TagUnawareMonitor,
    ) -> None:
        """Actions without tags should trigger both prepare() and done() normally"""
        result = await processor_with_tag_unaware.wait_for_complete(untagged_action)

        assert result.entity_id() == "untagged-1"
        assert tag_unaware_monitor.prepare_called is True
        assert tag_unaware_monitor.done_called is True
        assert tag_unaware_monitor.last_action == untagged_action

    @pytest.mark.asyncio
    async def test_tag_aware_monitor_skips_tagged_action(
        self,
        processor_with_tag_aware: ActionProcessor,
        tagged_action: MockActionWithTag,
        tag_aware_monitor: TagAwareMonitor,
    ) -> None:
        """TagAwareMonitor should skip logging for actions with SKIP_AUDIT_LOG tag"""
        await processor_with_tag_aware.wait_for_complete(tagged_action)

        assert tag_aware_monitor.prepare_called is True
        assert tag_aware_monitor.done_called is True
        assert tag_aware_monitor.log_generated is False  # Skipped due to tag

    @pytest.mark.asyncio
    async def test_tag_aware_monitor_logs_untagged_action(
        self,
        processor_with_tag_aware: ActionProcessor,
        untagged_action: MockActionWithoutTag,
        tag_aware_monitor: TagAwareMonitor,
    ) -> None:
        """TagAwareMonitor should generate logs for actions without SKIP_AUDIT_LOG tag"""
        await processor_with_tag_aware.wait_for_complete(untagged_action)

        assert tag_aware_monitor.prepare_called is True
        assert tag_aware_monitor.done_called is True
        assert tag_aware_monitor.log_generated is True  # Log generated for untagged action
