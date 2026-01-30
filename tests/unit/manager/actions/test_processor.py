from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Final

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
