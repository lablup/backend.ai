from __future__ import annotations

from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from ai.backend.common.dto.manager.operations.request import (
    AppendErrorLogRequest,
    ClearErrorLogPathParam,
    ListErrorLogsRequest,
    PerformSchedulerOpsRequest,
    PushBackgroundTaskEventsRequest,
    PushSessionEventsRequest,
    UpdateAnnouncementRequest,
    UpdateManagerStatusRequest,
)
from ai.backend.common.dto.manager.operations.response import (
    AppendErrorLogResponse,
    ClearErrorLogResponse,
    ErrorLogItem,
    FetchManagerStatusResponse,
    GetAnnouncementResponse,
    ListErrorLogsResponse,
    ManagerNodeInfo,
)
from ai.backend.common.dto.manager.operations.types import (
    ErrorLogSeverity,
    ManagerStatus,
    SchedulerOps,
)

# -------- SchedulerOps Enum --------


class TestSchedulerOps:
    def test_enum_values(self) -> None:
        assert SchedulerOps.INCLUDE_AGENTS.value == "include-agents"
        assert SchedulerOps.EXCLUDE_AGENTS.value == "exclude-agents"

    def test_is_str_enum(self) -> None:
        assert isinstance(SchedulerOps.INCLUDE_AGENTS, str)


# -------- Request Models: Logs --------


class TestAppendErrorLogRequest:
    def test_valid_creation(self) -> None:
        req = AppendErrorLogRequest(
            severity=ErrorLogSeverity.ERROR,
            source="webui",
            message="Something went wrong",
            context_lang="python",
            context_env='{"version": "3.11"}',
        )
        assert req.severity == ErrorLogSeverity.ERROR
        assert req.source == "webui"
        assert req.message == "Something went wrong"
        assert req.context_lang == "python"
        assert req.context_env == '{"version": "3.11"}'
        assert req.request_url is None
        assert req.request_status is None
        assert req.traceback is None

    def test_with_optional_fields(self) -> None:
        req = AppendErrorLogRequest(
            severity=ErrorLogSeverity.CRITICAL,
            source="manager",
            message="Fatal error",
            context_lang="python",
            context_env="{}",
            request_url="/v5/compute/sessions",
            request_status=500,
            traceback="Traceback (most recent call last):\n  ...",
        )
        assert req.request_url == "/v5/compute/sessions"
        assert req.request_status == 500
        assert req.traceback is not None

    def test_missing_required_field(self) -> None:
        with pytest.raises(ValidationError):
            AppendErrorLogRequest.model_validate({
                "severity": "error",
                "source": "webui",
                # missing message, context_lang, context_env
            })


class TestListErrorLogsRequest:
    def test_defaults(self) -> None:
        req = ListErrorLogsRequest()
        assert req.mark_read is False
        assert req.page_size == 20
        assert req.page_no == 1

    def test_custom_values(self) -> None:
        req = ListErrorLogsRequest(mark_read=True, page_size=50, page_no=3)
        assert req.mark_read is True
        assert req.page_size == 50
        assert req.page_no == 3

    def test_page_size_upper_bound(self) -> None:
        req = ListErrorLogsRequest(page_size=100)
        assert req.page_size == 100
        with pytest.raises(ValidationError):
            ListErrorLogsRequest(page_size=101)

    def test_page_size_lower_bound(self) -> None:
        req = ListErrorLogsRequest(page_size=1)
        assert req.page_size == 1
        with pytest.raises(ValidationError):
            ListErrorLogsRequest(page_size=0)

    def test_page_no_lower_bound(self) -> None:
        with pytest.raises(ValidationError):
            ListErrorLogsRequest(page_no=0)


class TestClearErrorLogPathParam:
    def test_valid_uuid(self) -> None:
        uid = uuid4()
        param = ClearErrorLogPathParam(log_id=uid)
        assert param.log_id == uid

    def test_uuid_from_string(self) -> None:
        uid_str = "550e8400-e29b-41d4-a716-446655440000"
        param = ClearErrorLogPathParam.model_validate({"log_id": uid_str})
        assert param.log_id == UUID(uid_str)


# -------- Request Models: Events --------


class TestPushSessionEventsRequest:
    def test_defaults(self) -> None:
        req = PushSessionEventsRequest()
        assert req.session_name == "*"
        assert req.owner_access_key is None
        assert req.session_id is None
        assert req.group_name == "*"
        assert req.scope == "*"

    def test_alias_session_name(self) -> None:
        req = PushSessionEventsRequest.model_validate({"sessionName": "my-session"})
        assert req.session_name == "my-session"

    def test_alias_name(self) -> None:
        req = PushSessionEventsRequest.model_validate({"name": "my-session"})
        assert req.session_name == "my-session"

    def test_alias_group_name(self) -> None:
        req = PushSessionEventsRequest.model_validate({"groupName": "my-group"})
        assert req.group_name == "my-group"

    def test_alias_group(self) -> None:
        req = PushSessionEventsRequest.model_validate({"group": "my-group"})
        assert req.group_name == "my-group"

    def test_alias_owner_access_key(self) -> None:
        req = PushSessionEventsRequest.model_validate({"ownerAccessKey": "AKTEST1234"})
        assert req.owner_access_key == "AKTEST1234"

    def test_alias_session_id(self) -> None:
        uid = uuid4()
        req = PushSessionEventsRequest.model_validate({"sessionId": str(uid)})
        assert req.session_id == uid

    def test_custom_scope(self) -> None:
        req = PushSessionEventsRequest(scope="session,kernel")
        assert req.scope == "session,kernel"


class TestPushBackgroundTaskEventsRequest:
    def test_valid_creation(self) -> None:
        uid = uuid4()
        req = PushBackgroundTaskEventsRequest(task_id=uid)
        assert req.task_id == uid

    def test_alias_task_id(self) -> None:
        uid = uuid4()
        req = PushBackgroundTaskEventsRequest.model_validate({"taskId": str(uid)})
        assert req.task_id == uid

    def test_missing_task_id(self) -> None:
        with pytest.raises(ValidationError):
            PushBackgroundTaskEventsRequest.model_validate({})


# -------- Request Models: Manager --------


class TestUpdateManagerStatusRequest:
    def test_valid_creation(self) -> None:
        req = UpdateManagerStatusRequest(status=ManagerStatus.FROZEN)
        assert req.status == ManagerStatus.FROZEN
        assert req.force_kill is False

    def test_force_kill(self) -> None:
        req = UpdateManagerStatusRequest(status=ManagerStatus.RUNNING, force_kill=True)
        assert req.force_kill is True


class TestUpdateAnnouncementRequest:
    def test_defaults(self) -> None:
        req = UpdateAnnouncementRequest()
        assert req.enabled is False
        assert req.message is None

    def test_enabled_with_message(self) -> None:
        req = UpdateAnnouncementRequest(enabled=True, message="System maintenance at 2am")
        assert req.enabled is True
        assert req.message == "System maintenance at 2am"

    def test_disabled(self) -> None:
        req = UpdateAnnouncementRequest(enabled=False)
        assert req.enabled is False


class TestPerformSchedulerOpsRequest:
    def test_include_agents(self) -> None:
        req = PerformSchedulerOpsRequest(
            op=SchedulerOps.INCLUDE_AGENTS,
            args=["agent-001", "agent-002"],
        )
        assert req.op == SchedulerOps.INCLUDE_AGENTS
        assert req.args == ["agent-001", "agent-002"]

    def test_exclude_agents(self) -> None:
        req = PerformSchedulerOpsRequest(
            op=SchedulerOps.EXCLUDE_AGENTS,
            args=["agent-003"],
        )
        assert req.op == SchedulerOps.EXCLUDE_AGENTS


# -------- Response Models: Logs --------


class TestErrorLogItem:
    def test_full_creation(self) -> None:
        item = ErrorLogItem(
            log_id="550e8400-e29b-41d4-a716-446655440000",
            created_at=1700000000.0,
            severity="error",
            source="webui",
            user="660e8400-e29b-41d4-a716-446655440000",
            is_read=False,
            message="Something went wrong",
            context_lang="python",
            context_env={"version": "3.11"},
            request_url="/v5/compute/sessions",
            request_status=500,
            traceback="Traceback ...",
            is_cleared=False,
        )
        assert item.log_id == "550e8400-e29b-41d4-a716-446655440000"
        assert item.created_at == 1700000000.0
        assert item.severity == "error"
        assert item.user == "660e8400-e29b-41d4-a716-446655440000"
        assert item.is_read is False
        assert item.request_status == 500
        assert item.is_cleared is False

    def test_optional_fields(self) -> None:
        item = ErrorLogItem(
            log_id="550e8400-e29b-41d4-a716-446655440000",
            created_at=1700000000.0,
            severity="warning",
            source="client",
            user=None,
            is_read=True,
            message="Minor issue",
            context_lang="javascript",
            context_env={},
            request_url=None,
            request_status=None,
            traceback=None,
        )
        assert item.user is None
        assert item.request_url is None
        assert item.request_status is None
        assert item.traceback is None
        assert item.is_cleared is None

    def test_serialization(self) -> None:
        item = ErrorLogItem(
            log_id="550e8400-e29b-41d4-a716-446655440000",
            created_at=1700000000.0,
            severity="error",
            source="webui",
            user=None,
            is_read=False,
            message="Error",
            context_lang="python",
            context_env={"key": "value"},
            request_url=None,
            request_status=None,
            traceback=None,
        )
        data = item.model_dump()
        assert data["log_id"] == "550e8400-e29b-41d4-a716-446655440000"
        assert data["created_at"] == 1700000000.0
        assert data["context_env"] == {"key": "value"}
        assert data["is_cleared"] is None


class TestAppendErrorLogResponse:
    def test_success(self) -> None:
        resp = AppendErrorLogResponse(success=True)
        assert resp.success is True

    def test_serialization(self) -> None:
        resp = AppendErrorLogResponse(success=True)
        assert resp.model_dump() == {"success": True}


class TestListErrorLogsResponse:
    def test_empty_logs(self) -> None:
        resp = ListErrorLogsResponse(logs=[], count=0)
        assert resp.logs == []
        assert resp.count == 0

    def test_with_logs(self) -> None:
        item = ErrorLogItem(
            log_id="550e8400-e29b-41d4-a716-446655440000",
            created_at=1700000000.0,
            severity="error",
            source="webui",
            user=None,
            is_read=False,
            message="Error",
            context_lang="python",
            context_env={},
            request_url=None,
            request_status=None,
            traceback=None,
        )
        resp = ListErrorLogsResponse(logs=[item], count=1)
        assert len(resp.logs) == 1
        assert resp.count == 1

    def test_serialization_roundtrip(self) -> None:
        item = ErrorLogItem(
            log_id="550e8400-e29b-41d4-a716-446655440000",
            created_at=1700000000.0,
            severity="error",
            source="webui",
            user=None,
            is_read=False,
            message="Error",
            context_lang="python",
            context_env={},
            request_url=None,
            request_status=None,
            traceback=None,
        )
        resp = ListErrorLogsResponse(logs=[item], count=1)
        data = resp.model_dump()
        roundtrip = ListErrorLogsResponse.model_validate(data)
        assert roundtrip.logs[0].log_id == item.log_id
        assert roundtrip.count == 1


class TestClearErrorLogResponse:
    def test_success(self) -> None:
        resp = ClearErrorLogResponse(success=True)
        assert resp.success is True


# -------- Response Models: Manager --------


class TestManagerNodeInfo:
    def test_creation(self) -> None:
        node = ManagerNodeInfo(
            id="manager-01",
            num_proc=4,
            service_addr="0.0.0.0:8081",
            heartbeat_timeout=30.0,
            ssl_enabled=False,
            active_sessions=5,
            status="running",
            version="24.09.0",
            api_version=8,
        )
        assert node.id == "manager-01"
        assert node.num_proc == 4
        assert node.service_addr == "0.0.0.0:8081"
        assert node.heartbeat_timeout == 30.0
        assert node.ssl_enabled is False
        assert node.active_sessions == 5
        assert node.status == "running"
        assert node.version == "24.09.0"
        assert node.api_version == 8


class TestFetchManagerStatusResponse:
    def test_creation(self) -> None:
        node = ManagerNodeInfo(
            id="manager-01",
            num_proc=4,
            service_addr="0.0.0.0:8081",
            heartbeat_timeout=30.0,
            ssl_enabled=False,
            active_sessions=5,
            status="running",
            version="24.09.0",
            api_version=8,
        )
        resp = FetchManagerStatusResponse(
            nodes=[node],
            status="running",
            active_sessions=5,
        )
        assert len(resp.nodes) == 1
        assert resp.status == "running"
        assert resp.active_sessions == 5

    def test_serialization(self) -> None:
        node = ManagerNodeInfo(
            id="mgr-1",
            num_proc=2,
            service_addr="127.0.0.1:8081",
            heartbeat_timeout=60.0,
            ssl_enabled=True,
            active_sessions=0,
            status="frozen",
            version="24.09.0",
            api_version=8,
        )
        resp = FetchManagerStatusResponse(
            nodes=[node],
            status="frozen",
            active_sessions=0,
        )
        data = resp.model_dump()
        assert data["nodes"][0]["id"] == "mgr-1"
        assert data["status"] == "frozen"


class TestGetAnnouncementResponse:
    def test_enabled(self) -> None:
        resp = GetAnnouncementResponse(enabled=True, message="Maintenance tonight")
        assert resp.enabled is True
        assert resp.message == "Maintenance tonight"

    def test_disabled(self) -> None:
        resp = GetAnnouncementResponse(enabled=False, message="")
        assert resp.enabled is False
        assert resp.message == ""
