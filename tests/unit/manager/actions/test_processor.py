from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Final, Optional
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from ai.backend.common.data.agent.types import AgentInfo
from ai.backend.common.exception import ErrorCode
from ai.backend.common.types import AgentId
from ai.backend.manager.actions.action import (
    BaseAction,
    BaseActionResult,
    BaseActionResultMeta,
    BaseActionTriggerMeta,
    ProcessResult,
)
from ai.backend.manager.actions.monitors.audit_log import AuditLogMonitor
from ai.backend.manager.actions.monitors.exclusions import AUDIT_LOG_EXCLUDED_ACTIONS
from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import ActionSpec
from ai.backend.manager.repositories.audit_log import AuditLogRepository
from ai.backend.manager.services.agent.actions.handle_heartbeat import (
    HandleHeartbeatAction,
    HandleHeartbeatActionResult,
)

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


class TestHeartbeatExcludedFromAuditLog:
    """Test that heartbeat action is excluded from audit logging.

    This verifies the production configuration where high-frequency heartbeat
    actions are excluded to prevent excessive audit log entries.
    """

    def test_heartbeat_action_spec_is_in_exclusion_list(self) -> None:
        """HandleHeartbeatAction.spec() should be in AUDIT_LOG_EXCLUDED_ACTIONS."""
        heartbeat_spec = HandleHeartbeatAction.spec()

        assert heartbeat_spec in AUDIT_LOG_EXCLUDED_ACTIONS
        assert heartbeat_spec.entity_type == "agent"
        assert heartbeat_spec.operation_type == "handle_heartbeat"

    @pytest.fixture
    def mock_heartbeat_action(self) -> HandleHeartbeatAction:
        return HandleHeartbeatAction(
            agent_id=AgentId(f"{uuid4()}"), agent_info=MagicMock(spec=AgentInfo)
        )

    @pytest.fixture
    def mock_audit_log_repository(self) -> MagicMock:
        """Mock AuditLogRepository to track create() calls."""
        return MagicMock(spec=AuditLogRepository)

    @pytest.fixture
    def audit_log_monitor(self, mock_audit_log_repository: MagicMock) -> AuditLogMonitor:
        """Real AuditLogMonitor with mocked repository."""
        return AuditLogMonitor(repository=mock_audit_log_repository)

    @pytest.fixture
    def heartbeat_processor_with_audit_monitor(
        self,
        audit_log_monitor: AuditLogMonitor,
    ) -> ActionProcessor[HandleHeartbeatAction, HandleHeartbeatActionResult]:
        async def _mock_heartbeat_func(
            action: HandleHeartbeatAction,
        ) -> HandleHeartbeatActionResult:
            return HandleHeartbeatActionResult(agent_id=action.agent_id)

        return ActionProcessor(
            func=_mock_heartbeat_func,
            monitors=[audit_log_monitor],
        )

    @pytest.mark.asyncio
    async def test_audit_log_monitor_skips_heartbeat_action(
        self,
        mock_heartbeat_action: HandleHeartbeatAction,
        heartbeat_processor_with_audit_monitor: ActionProcessor[
            HandleHeartbeatAction, HandleHeartbeatActionResult
        ],
        mock_audit_log_repository: MagicMock,
    ) -> None:
        """AuditLogMonitor should not call repository.create() for heartbeat actions."""
        await heartbeat_processor_with_audit_monitor.wait_for_complete(mock_heartbeat_action)

        # Verify that repository.create() was NOT called for heartbeat action
        mock_audit_log_repository.create.assert_not_called()
