from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Final, override
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from ai.backend.common.data.permission.types import EntityType
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
from ai.backend.manager.actions.types import ActionOperationType, OperationStatus

_MOCK_ACTION_TYPE: Final[str] = "test"
_MOCK_OPERATION_TYPE: Final[str] = "create"


@dataclass
class MockAction(BaseAction):
    id: str
    type: str
    operation: str

    @override
    def entity_id(self) -> str | None:
        return self.id

    @classmethod
    @override
    def entity_type(cls) -> EntityType:
        return EntityType.SESSION

    @classmethod
    @override
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


@dataclass
class MockActionResult(BaseActionResult):
    id: str

    @override
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

    @override
    async def prepare(self, action: BaseAction, meta: BaseActionTriggerMeta) -> None:
        assert isinstance(action, MockAction)
        assert action == self.expected_prepare_action

    @override
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


class TestAuditLogMonitorExclusionAtSetupTime:
    @pytest.fixture
    def mock_audit_log_repository(self) -> MagicMock:
        repo = MagicMock()
        repo.create = AsyncMock(return_value=None)
        return repo

    @pytest.fixture
    def audit_log_monitor(self, mock_audit_log_repository: MagicMock) -> AuditLogMonitor:
        return AuditLogMonitor(repository=mock_audit_log_repository)

    @pytest.fixture
    def mock_action(self) -> MockAction:
        return MockAction(id="1", type=_MOCK_ACTION_TYPE, operation=_MOCK_OPERATION_TYPE)

    async def test_audit_log_monitor_excluded_when_filtered_from_monitor_list(
        self,
        audit_log_monitor: AuditLogMonitor,
        mock_audit_log_repository: MagicMock,
        mock_action: MockAction,
    ) -> None:
        monitors_without_audit_log = [
            monitor for monitor in [audit_log_monitor] if not isinstance(monitor, AuditLogMonitor)
        ]
        processor = ActionProcessor[MockAction, MockActionResult](
            func=mock_action_processor_func, monitors=monitors_without_audit_log
        )

        await processor.wait_for_complete(mock_action)

        mock_audit_log_repository.create.assert_not_called()
