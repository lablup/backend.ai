from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Final, override
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest

from ai.backend.common.contexts.user import with_triggered_user, with_user
from ai.backend.common.data.permission.types import EntityType
from ai.backend.common.data.user.types import UserData, UserRole
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
from ai.backend.manager.actions.monitors.reporter import ReporterMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import ActionOperationType, OperationStatus
from ai.backend.manager.repositories.audit_log import AuditLogCreatorSpec

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


def _make_user(user_id: UUID, is_superadmin: bool = False) -> UserData:
    return UserData(
        user_id=user_id,
        is_authorized=True,
        is_admin=is_superadmin,
        is_superadmin=is_superadmin,
        role=UserRole.SUPERADMIN if is_superadmin else UserRole.USER,
        domain_name="default",
    )


class TestAuditLogMonitorActorIdentities:
    """AuditLogMonitor records the trigger identity (triggered_by) and the effective/acting
    identity (acted_as) separately; they diverge only during impersonation."""

    @pytest.fixture
    def mock_audit_log_repository(self) -> MagicMock:
        repo = MagicMock()
        repo.create = AsyncMock(return_value=None)
        return repo

    @pytest.fixture
    def audit_log_monitor(self, mock_audit_log_repository: MagicMock) -> AuditLogMonitor:
        return AuditLogMonitor(repository=mock_audit_log_repository)

    def _result(self) -> ProcessResult:
        now = datetime.now(tz=UTC)
        return ProcessResult(
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
        )

    def _recorded_spec(self, mock_audit_log_repository: MagicMock) -> AuditLogCreatorSpec:
        mock_audit_log_repository.create.assert_called_once()
        spec: AuditLogCreatorSpec = mock_audit_log_repository.create.call_args.args[0].spec
        return spec

    async def test_normal_context_triggered_by_equals_acted_as(
        self,
        audit_log_monitor: AuditLogMonitor,
        mock_audit_log_repository: MagicMock,
    ) -> None:
        user = _make_user(uuid4())
        action = MockAction(id="1", type=_MOCK_ACTION_TYPE, operation=_MOCK_OPERATION_TYPE)

        with with_user(user), with_triggered_user(user):
            await audit_log_monitor.done(action, self._result())

        spec = self._recorded_spec(mock_audit_log_repository)
        assert spec.triggered_by == str(user.user_id)
        assert spec.acted_as == str(user.user_id)

    async def test_impersonation_records_both_identities(
        self,
        audit_log_monitor: AuditLogMonitor,
        mock_audit_log_repository: MagicMock,
    ) -> None:
        target = _make_user(uuid4())
        super_admin = _make_user(uuid4(), is_superadmin=True)
        action = MockAction(id="1", type=_MOCK_ACTION_TYPE, operation=_MOCK_OPERATION_TYPE)

        with with_user(target), with_triggered_user(super_admin):
            await audit_log_monitor.done(action, self._result())

        spec = self._recorded_spec(mock_audit_log_repository)
        assert spec.triggered_by == str(super_admin.user_id)
        assert spec.acted_as == str(target.user_id)

    async def test_system_trigger_records_both_none(
        self,
        audit_log_monitor: AuditLogMonitor,
        mock_audit_log_repository: MagicMock,
    ) -> None:
        action = MockAction(id="1", type=_MOCK_ACTION_TYPE, operation=_MOCK_OPERATION_TYPE)

        await audit_log_monitor.done(action, self._result())

        spec = self._recorded_spec(mock_audit_log_repository)
        assert spec.triggered_by is None
        assert spec.acted_as is None


@dataclass(frozen=True)
class _ExpectedActorIdentities:
    """The (triggered_by, acted_as) a reporter message should record for a context."""

    triggered_by: str | None
    acted_as: UUID | None


class TestReporterMonitorActorIdentities:
    """ReporterMonitor records triggered_by (the caller) and acted_as (the effective/acting
    subject) separately, mirroring the audit-log monitor; they diverge only during
    impersonation."""

    @pytest.fixture
    def reporter_hub(self) -> MagicMock:
        hub = MagicMock()
        hub.report_started = AsyncMock(return_value=None)
        hub.report_finished = AsyncMock(return_value=None)
        return hub

    @pytest.fixture
    def reporter_monitor(self, reporter_hub: MagicMock) -> ReporterMonitor:
        return ReporterMonitor(reporter_hub)

    @pytest.fixture
    def mock_action(self) -> MockAction:
        return MockAction(id="1", type=_MOCK_ACTION_TYPE, operation=_MOCK_OPERATION_TYPE)

    @pytest.fixture
    def mock_meta(self) -> BaseActionTriggerMeta:
        return BaseActionTriggerMeta(action_id=uuid4(), started_at=datetime.now(tz=UTC))

    @pytest.fixture
    def mock_result(self) -> ProcessResult:
        now = datetime.now(tz=UTC)
        return ProcessResult(
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
        )

    @pytest.fixture
    def impersonation_context(self) -> Iterator[_ExpectedActorIdentities]:
        """Super admin acting as another user: caller and effective subject differ."""
        target = _make_user(uuid4())
        super_admin = _make_user(uuid4(), is_superadmin=True)
        with with_user(target), with_triggered_user(super_admin):
            yield _ExpectedActorIdentities(
                triggered_by=str(super_admin.user_id), acted_as=target.user_id
            )

    @pytest.fixture
    def normal_context(self) -> Iterator[_ExpectedActorIdentities]:
        """Caller and effective subject are the same user."""
        user = _make_user(uuid4())
        with with_user(user), with_triggered_user(user):
            yield _ExpectedActorIdentities(triggered_by=str(user.user_id), acted_as=user.user_id)

    @pytest.fixture
    def system_context(self) -> Iterator[_ExpectedActorIdentities]:
        """System-triggered action: no authenticated user."""
        yield _ExpectedActorIdentities(triggered_by=None, acted_as=None)

    async def test_impersonation_records_caller_and_effective_identities(
        self,
        reporter_monitor: ReporterMonitor,
        reporter_hub: MagicMock,
        mock_action: MockAction,
        mock_meta: BaseActionTriggerMeta,
        mock_result: ProcessResult,
        impersonation_context: _ExpectedActorIdentities,
    ) -> None:
        expected = impersonation_context

        await reporter_monitor.prepare(mock_action, mock_meta)
        await reporter_monitor.done(mock_action, mock_result)

        started = reporter_hub.report_started.call_args.args[0]
        finished = reporter_hub.report_finished.call_args.args[0]
        assert started.triggered_by == finished.triggered_by == expected.triggered_by
        assert started.acted_as == finished.acted_as == expected.acted_as

    async def test_normal_context_triggered_by_equals_acted_as(
        self,
        reporter_monitor: ReporterMonitor,
        reporter_hub: MagicMock,
        mock_action: MockAction,
        mock_meta: BaseActionTriggerMeta,
        mock_result: ProcessResult,
        normal_context: _ExpectedActorIdentities,
    ) -> None:
        expected = normal_context

        await reporter_monitor.prepare(mock_action, mock_meta)
        await reporter_monitor.done(mock_action, mock_result)

        started = reporter_hub.report_started.call_args.args[0]
        finished = reporter_hub.report_finished.call_args.args[0]
        assert started.triggered_by == finished.triggered_by == expected.triggered_by
        assert started.acted_as == finished.acted_as == expected.acted_as

    async def test_system_trigger_records_both_none(
        self,
        reporter_monitor: ReporterMonitor,
        reporter_hub: MagicMock,
        mock_action: MockAction,
        mock_meta: BaseActionTriggerMeta,
        mock_result: ProcessResult,
        system_context: _ExpectedActorIdentities,
    ) -> None:
        expected = system_context

        await reporter_monitor.prepare(mock_action, mock_meta)
        await reporter_monitor.done(mock_action, mock_result)

        started = reporter_hub.report_started.call_args.args[0]
        finished = reporter_hub.report_finished.call_args.args[0]
        assert started.triggered_by == finished.triggered_by == expected.triggered_by
        assert started.acted_as == finished.acted_as == expected.acted_as
