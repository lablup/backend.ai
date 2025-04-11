from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import pytest
from tenacity import BaseAction

from ai.backend.manager.actions.action import BaseActionResult, BaseActionResultMeta, ProcessResult
from ai.backend.manager.actions.processor import ActionProcessor


@dataclass
class MockAction(BaseAction):
    id: str
    type: str
    operation: str

    def entity_id(self) -> Optional[str]:
        return self.id

    def entity_type(self) -> str:
        return self.type

    def operation_type(self) -> str:
        return self.operation


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
    expected_done_result: ProcessResult[MockActionResult]

    def __init__(
        self,
        expected_prepare_action: MockAction,
        expected_done_action: MockAction,
        expected_done_result: ProcessResult[MockActionResult],
    ):
        self.expected_prepare_action = expected_prepare_action
        self.expected_done_action = expected_done_action
        self.expected_done_result = expected_done_result

    async def prepare(self, action: MockAction, _meta: MockActionTriggerMeta) -> None:
        assert action == self.expected_prepare_action

    async def done(self, action: MockAction, result: ProcessResult[MockActionResult]) -> None:
        assert action == self.expected_done_action
        # Partially check the result
        assert result.meta.status == self.expected_done_result.meta.status
        assert result.meta.description == self.expected_done_result.meta.description
        current_time = datetime.now()
        assert result.meta.started_at < current_time
        assert result.meta.started_at <= result.meta.end_at
        assert result.meta.end_at < current_time
        assert result.meta.duration >= 0
        if self.expected_done_result.result:
            assert result.result is not None
            assert result.result.entity_id() == self.expected_done_result.result.entity_id()
        else:
            assert result.result is None


async def mock_action_processor_func(action: MockAction) -> MockActionResult:
    return MockActionResult(id=action.id)


async def mock_exception_processor_func(action: MockAction) -> MockActionResult:
    raise MockException("Mock exception")


async def test_processor_success():
    monitor = MockActionMonitor(
        expected_prepare_action=MockAction(id="1", type="test", operation="create"),
        expected_done_action=MockAction(id="1", type="test", operation="create"),
        expected_done_result=ProcessResult(
            meta=BaseActionResultMeta(
                task_id=None,
                status="success",
                description="Success",
                started_at=None,
                end_at=None,
                duration=0.0,
            ),
            result=MockActionResult(id="1"),
        ),
    )
    processor = ActionProcessor[MockAction, MockActionResult](
        func=mock_action_processor_func, monitors=[monitor]
    )
    action = MockAction(id="1", type="test", operation="create")
    result = await processor.wait_for_complete(action)

    assert result.entity_id() == "1"


async def test_processor_exception():
    monitor = MockActionMonitor(
        expected_prepare_action=MockAction(id="1", type="test", operation="create"),
        expected_done_action=MockAction(id="1", type="test", operation="create"),
        expected_done_result=ProcessResult(
            meta=BaseActionResultMeta(
                task_id=None,
                status="error",
                description="Mock exception",
                started_at=None,
                end_at=None,
                duration=0.0,
            ),
            result=None,
        ),
    )
    processor = ActionProcessor[MockAction, MockActionResult](
        func=mock_exception_processor_func, monitors=[monitor]
    )
    action = MockAction(id="1", type="test", operation="create")

    with pytest.raises(MockException):
        await processor.wait_for_complete(action)
