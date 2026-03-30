"""Tests for ai.backend.common.dto.manager.v2.operations.request module."""

from __future__ import annotations

import uuid

import pytest
from pydantic import ValidationError

from ai.backend.common.dto.manager.operations.types import (
    ErrorLogSeverity,
    ManagerStatus,
    SchedulerOps,
)
from ai.backend.common.dto.manager.v2.operations.request import (
    AppendErrorLogInput,
    ClearErrorLogInput,
    ListErrorLogsInput,
    PerformSchedulerOpsInput,
    SubscribeBackgroundTaskInput,
    SubscribeSessionEventsInput,
    UpdateAnnouncementInput,
    UpdateManagerStatusInput,
)


class TestAppendErrorLogInput:
    """Tests for AppendErrorLogInput model creation and validation."""

    def test_valid_creation_with_required_fields(self) -> None:
        req = AppendErrorLogInput(
            severity=ErrorLogSeverity.ERROR,
            source="manager",
            message="Something went wrong",
            context_lang="python",
            context_env="{}",
        )
        assert req.severity == ErrorLogSeverity.ERROR
        assert req.source == "manager"
        assert req.message == "Something went wrong"
        assert req.context_lang == "python"
        assert req.context_env == "{}"

    def test_default_optional_fields_are_none(self) -> None:
        req = AppendErrorLogInput(
            severity=ErrorLogSeverity.WARNING,
            source="agent",
            message="Warning occurred",
            context_lang="python",
            context_env="{}",
        )
        assert req.request_url is None
        assert req.request_status is None
        assert req.traceback is None

    def test_accepts_critical_severity(self) -> None:
        req = AppendErrorLogInput(
            severity=ErrorLogSeverity.CRITICAL,
            source="storage",
            message="Critical failure",
            context_lang="python",
            context_env="{}",
        )
        assert req.severity == ErrorLogSeverity.CRITICAL

    def test_accepts_warning_severity(self) -> None:
        req = AppendErrorLogInput(
            severity=ErrorLogSeverity.WARNING,
            source="manager",
            message="Low disk space",
            context_lang="python",
            context_env="{}",
        )
        assert req.severity == ErrorLogSeverity.WARNING

    def test_creation_with_all_fields(self) -> None:
        req = AppendErrorLogInput(
            severity=ErrorLogSeverity.ERROR,
            source="manager",
            message="Error occurred",
            context_lang="python",
            context_env='{"DEBUG": "true"}',
            request_url="/api/v2/session",
            request_status=500,
            traceback="Traceback (most recent call last)...",
        )
        assert req.request_url == "/api/v2/session"
        assert req.request_status == 500
        assert req.traceback == "Traceback (most recent call last)..."

    def test_missing_severity_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            AppendErrorLogInput.model_validate({
                "source": "manager",
                "message": "Error",
                "context_lang": "python",
                "context_env": "{}",
            })

    def test_missing_source_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            AppendErrorLogInput.model_validate({
                "severity": "error",
                "message": "Error",
                "context_lang": "python",
                "context_env": "{}",
            })

    def test_missing_message_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            AppendErrorLogInput.model_validate({
                "severity": "error",
                "source": "manager",
                "context_lang": "python",
                "context_env": "{}",
            })

    def test_severity_from_string_value(self) -> None:
        req = AppendErrorLogInput.model_validate({
            "severity": "critical",
            "source": "manager",
            "message": "Critical",
            "context_lang": "python",
            "context_env": "{}",
        })
        assert req.severity == ErrorLogSeverity.CRITICAL

    def test_invalid_severity_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            AppendErrorLogInput.model_validate({
                "severity": "debug",
                "source": "manager",
                "message": "Error",
                "context_lang": "python",
                "context_env": "{}",
            })


class TestListErrorLogsInput:
    """Tests for ListErrorLogsInput model creation and validation."""

    def test_default_values(self) -> None:
        req = ListErrorLogsInput()
        assert req.mark_read is False
        assert req.page_size == 20
        assert req.page_no == 1

    def test_valid_custom_page_size(self) -> None:
        req = ListErrorLogsInput(page_size=50)
        assert req.page_size == 50

    def test_valid_min_page_size(self) -> None:
        req = ListErrorLogsInput(page_size=1)
        assert req.page_size == 1

    def test_valid_max_page_size(self) -> None:
        req = ListErrorLogsInput(page_size=100)
        assert req.page_size == 100

    def test_valid_page_no(self) -> None:
        req = ListErrorLogsInput(page_no=5)
        assert req.page_no == 5

    def test_mark_read_true(self) -> None:
        req = ListErrorLogsInput(mark_read=True)
        assert req.mark_read is True

    def test_page_size_below_min_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            ListErrorLogsInput(page_size=0)

    def test_page_size_above_max_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            ListErrorLogsInput(page_size=101)

    def test_page_no_below_min_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            ListErrorLogsInput(page_no=0)

    def test_negative_page_size_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            ListErrorLogsInput(page_size=-1)

    def test_negative_page_no_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            ListErrorLogsInput(page_no=-1)


class TestClearErrorLogInput:
    """Tests for ClearErrorLogInput model creation and validation."""

    def test_valid_creation_with_uuid(self) -> None:
        log_id = uuid.uuid4()
        req = ClearErrorLogInput(log_id=log_id)
        assert req.log_id == log_id

    def test_valid_creation_from_uuid_string(self) -> None:
        log_id = uuid.uuid4()
        req = ClearErrorLogInput.model_validate({"log_id": str(log_id)})
        assert req.log_id == log_id

    def test_invalid_uuid_string_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            ClearErrorLogInput.model_validate({"log_id": "not-a-uuid"})

    def test_missing_log_id_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            ClearErrorLogInput.model_validate({})

    def test_log_id_is_uuid_instance(self) -> None:
        log_id = uuid.uuid4()
        req = ClearErrorLogInput(log_id=log_id)
        assert isinstance(req.log_id, uuid.UUID)

    def test_round_trip_uuid(self) -> None:
        log_id = uuid.uuid4()
        req = ClearErrorLogInput(log_id=log_id)
        json_str = req.model_dump_json()
        restored = ClearErrorLogInput.model_validate_json(json_str)
        assert restored.log_id == log_id


class TestUpdateManagerStatusInput:
    """Tests for UpdateManagerStatusInput model creation and validation."""

    def test_valid_creation_with_running_status(self) -> None:
        req = UpdateManagerStatusInput(status=ManagerStatus.RUNNING)
        assert req.status == ManagerStatus.RUNNING
        assert req.force_kill is False

    def test_valid_creation_with_frozen_status(self) -> None:
        req = UpdateManagerStatusInput(status=ManagerStatus.FROZEN)
        assert req.status == ManagerStatus.FROZEN

    def test_valid_creation_with_terminated_status(self) -> None:
        req = UpdateManagerStatusInput(status=ManagerStatus.TERMINATED)
        assert req.status == ManagerStatus.TERMINATED

    def test_valid_creation_with_preparing_status(self) -> None:
        req = UpdateManagerStatusInput(status=ManagerStatus.PREPARING)
        assert req.status == ManagerStatus.PREPARING

    def test_default_force_kill_is_false(self) -> None:
        req = UpdateManagerStatusInput(status=ManagerStatus.RUNNING)
        assert req.force_kill is False

    def test_force_kill_true(self) -> None:
        req = UpdateManagerStatusInput(status=ManagerStatus.FROZEN, force_kill=True)
        assert req.force_kill is True

    def test_status_from_string_value(self) -> None:
        req = UpdateManagerStatusInput.model_validate({"status": "running"})
        assert req.status == ManagerStatus.RUNNING

    def test_invalid_status_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            UpdateManagerStatusInput.model_validate({"status": "invalid-status"})

    def test_missing_status_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            UpdateManagerStatusInput.model_validate({})


class TestUpdateAnnouncementInput:
    """Tests for UpdateAnnouncementInput model creation and validation."""

    def test_default_values(self) -> None:
        req = UpdateAnnouncementInput()
        assert req.enabled is False
        assert req.message is None

    def test_enabled_true_with_message(self) -> None:
        req = UpdateAnnouncementInput(enabled=True, message="System maintenance tonight")
        assert req.enabled is True
        assert req.message == "System maintenance tonight"

    def test_enabled_false_with_no_message(self) -> None:
        req = UpdateAnnouncementInput(enabled=False)
        assert req.enabled is False
        assert req.message is None

    def test_enabled_false_with_message(self) -> None:
        req = UpdateAnnouncementInput(enabled=False, message="Some message")
        assert req.enabled is False
        assert req.message == "Some message"

    def test_explicit_none_message(self) -> None:
        req = UpdateAnnouncementInput(enabled=True, message=None)
        assert req.message is None


class TestPerformSchedulerOpsInput:
    """Tests for PerformSchedulerOpsInput model creation and validation."""

    def test_valid_creation_with_include_agents(self) -> None:
        req = PerformSchedulerOpsInput(
            op=SchedulerOps.INCLUDE_AGENTS,
            args=["agent-01", "agent-02"],
        )
        assert req.op == SchedulerOps.INCLUDE_AGENTS
        assert req.args == ["agent-01", "agent-02"]

    def test_valid_creation_with_exclude_agents(self) -> None:
        req = PerformSchedulerOpsInput(
            op=SchedulerOps.EXCLUDE_AGENTS,
            args=["agent-03"],
        )
        assert req.op == SchedulerOps.EXCLUDE_AGENTS
        assert req.args == ["agent-03"]

    def test_valid_creation_with_empty_args(self) -> None:
        req = PerformSchedulerOpsInput(op=SchedulerOps.INCLUDE_AGENTS, args=[])
        assert req.args == []

    def test_op_from_string_value(self) -> None:
        req = PerformSchedulerOpsInput.model_validate({
            "op": "include-agents",
            "args": ["agent-01"],
        })
        assert req.op == SchedulerOps.INCLUDE_AGENTS

    def test_op_from_exclude_string_value(self) -> None:
        req = PerformSchedulerOpsInput.model_validate({
            "op": "exclude-agents",
            "args": [],
        })
        assert req.op == SchedulerOps.EXCLUDE_AGENTS

    def test_invalid_op_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            PerformSchedulerOpsInput.model_validate({
                "op": "invalid-op",
                "args": [],
            })

    def test_missing_op_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            PerformSchedulerOpsInput.model_validate({"args": []})

    def test_missing_args_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            PerformSchedulerOpsInput.model_validate({"op": "include-agents"})


class TestSubscribeSessionEventsInput:
    """Tests for SubscribeSessionEventsInput model creation and validation."""

    def test_default_values(self) -> None:
        req = SubscribeSessionEventsInput()
        assert req.session_name == "*"
        assert req.owner_access_key is None
        assert req.session_id is None
        assert req.group_name == "*"
        assert req.scope == "*"

    def test_custom_session_name(self) -> None:
        req = SubscribeSessionEventsInput(session_name="my-session")
        assert req.session_name == "my-session"

    def test_accepts_session_id_uuid(self) -> None:
        session_id = uuid.uuid4()
        req = SubscribeSessionEventsInput(session_id=session_id)
        assert req.session_id == session_id

    def test_accepts_owner_access_key(self) -> None:
        req = SubscribeSessionEventsInput(owner_access_key="AKIAIOSFODNN7EXAMPLE")
        assert req.owner_access_key == "AKIAIOSFODNN7EXAMPLE"

    def test_accepts_custom_group_name(self) -> None:
        req = SubscribeSessionEventsInput(group_name="research-group")
        assert req.group_name == "research-group"

    def test_accepts_custom_scope(self) -> None:
        req = SubscribeSessionEventsInput(scope="session,kernel")
        assert req.scope == "session,kernel"


class TestSubscribeBackgroundTaskInput:
    """Tests for SubscribeBackgroundTaskInput model creation and validation."""

    def test_valid_creation_with_uuid(self) -> None:
        task_id = uuid.uuid4()
        req = SubscribeBackgroundTaskInput(task_id=task_id)
        assert req.task_id == task_id

    def test_valid_creation_from_uuid_string(self) -> None:
        task_id = uuid.uuid4()
        req = SubscribeBackgroundTaskInput.model_validate({"task_id": str(task_id)})
        assert req.task_id == task_id

    def test_invalid_uuid_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            SubscribeBackgroundTaskInput.model_validate({"task_id": "not-a-uuid"})

    def test_missing_task_id_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            SubscribeBackgroundTaskInput.model_validate({})

    def test_task_id_is_uuid_instance(self) -> None:
        task_id = uuid.uuid4()
        req = SubscribeBackgroundTaskInput(task_id=task_id)
        assert isinstance(req.task_id, uuid.UUID)

    def test_round_trip_uuid(self) -> None:
        task_id = uuid.uuid4()
        req = SubscribeBackgroundTaskInput(task_id=task_id)
        json_str = req.model_dump_json()
        restored = SubscribeBackgroundTaskInput.model_validate_json(json_str)
        assert restored.task_id == task_id
