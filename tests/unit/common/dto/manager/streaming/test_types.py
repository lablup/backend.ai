"""
Unit tests for streaming domain Pydantic types.
"""

from uuid import uuid4

import pytest
from pydantic import TypeAdapter, ValidationError

from ai.backend.common.dto.manager.streaming.types import (
    BackgroundTaskEventParams,
    BgtaskCancelledPayload,
    BgtaskDonePayload,
    BgtaskFailedPayload,
    BgtaskPartialSuccessPayload,
    BgtaskSSEEventName,
    BgtaskUpdatedPayload,
    ExecuteMode,
    ExecuteRequest,
    ExecuteResult,
    ExecuteResultStatus,
    PtyClientMessage,
    PtyInputMessageType,
    PtyOutputMessage,
    PtyOutputMessageType,
    PtyPingMessage,
    PtyResizeMessage,
    PtyRestartMessage,
    PtyStdinMessage,
    ServiceProtocol,
    SessionEventParams,
    SessionEventScope,
    StreamAppInfo,
    StreamProxyParams,
)

_pty_client_adapter: TypeAdapter[PtyClientMessage] = TypeAdapter(PtyClientMessage)

# ============================
# Enum Tests
# ============================


class TestPtyInputMessageType:
    def test_values(self) -> None:
        assert PtyInputMessageType.STDIN.value == "stdin"
        assert PtyInputMessageType.RESIZE.value == "resize"
        assert PtyInputMessageType.PING.value == "ping"
        assert PtyInputMessageType.RESTART.value == "restart"

    def test_members_count(self) -> None:
        assert len(PtyInputMessageType) == 4


class TestPtyOutputMessageType:
    def test_values(self) -> None:
        assert PtyOutputMessageType.OUT.value == "out"

    def test_members_count(self) -> None:
        assert len(PtyOutputMessageType) == 1


class TestExecuteMode:
    def test_values(self) -> None:
        assert ExecuteMode.QUERY.value == "query"
        assert ExecuteMode.BATCH.value == "batch"

    def test_members_count(self) -> None:
        assert len(ExecuteMode) == 2


class TestExecuteResultStatus:
    def test_values(self) -> None:
        assert ExecuteResultStatus.WAITING_INPUT.value == "waiting-input"
        assert ExecuteResultStatus.FINISHED.value == "finished"
        assert ExecuteResultStatus.ERROR.value == "error"
        assert ExecuteResultStatus.SERVER_RESTARTING.value == "server-restarting"

    def test_members_count(self) -> None:
        assert len(ExecuteResultStatus) == 4


class TestServiceProtocol:
    def test_values(self) -> None:
        assert ServiceProtocol.TCP.value == "tcp"
        assert ServiceProtocol.HTTP.value == "http"
        assert ServiceProtocol.PREOPEN.value == "preopen"
        assert ServiceProtocol.VNC.value == "vnc"
        assert ServiceProtocol.RDP.value == "rdp"

    def test_members_count(self) -> None:
        assert len(ServiceProtocol) == 5


class TestSessionEventScope:
    def test_values(self) -> None:
        assert SessionEventScope.SESSION.value == "session"
        assert SessionEventScope.KERNEL.value == "kernel"

    def test_members_count(self) -> None:
        assert len(SessionEventScope) == 2


class TestBgtaskSSEEventName:
    def test_values(self) -> None:
        assert BgtaskSSEEventName.BGTASK_UPDATED.value == "bgtask_updated"
        assert BgtaskSSEEventName.BGTASK_DONE.value == "bgtask_done"
        assert BgtaskSSEEventName.BGTASK_CANCELLED.value == "bgtask_cancelled"
        assert BgtaskSSEEventName.BGTASK_FAILED.value == "bgtask_failed"

    def test_members_count(self) -> None:
        assert len(BgtaskSSEEventName) == 4


# ============================
# PTY WebSocket Message Tests
# ============================


class TestPtyStdinMessage:
    def test_valid(self) -> None:
        msg = PtyStdinMessage(type=PtyInputMessageType.STDIN, chars="aGVsbG8=")
        assert msg.type == PtyInputMessageType.STDIN
        assert msg.chars == "aGVsbG8="

    def test_missing_chars(self) -> None:
        with pytest.raises(ValidationError):
            PtyStdinMessage(type=PtyInputMessageType.STDIN)  # type: ignore[call-arg]

    def test_rejects_extra_fields(self) -> None:
        with pytest.raises(ValidationError):
            PtyStdinMessage(type=PtyInputMessageType.STDIN, chars="abc", extra="bad")  # type: ignore[call-arg]


class TestPtyResizeMessage:
    def test_valid(self) -> None:
        msg = PtyResizeMessage(type=PtyInputMessageType.RESIZE, rows=24, cols=80)
        assert msg.type == PtyInputMessageType.RESIZE
        assert msg.rows == 24
        assert msg.cols == 80

    def test_missing_dimensions(self) -> None:
        with pytest.raises(ValidationError):
            PtyResizeMessage(type=PtyInputMessageType.RESIZE, rows=24)  # type: ignore[call-arg]

    def test_rejects_extra_fields(self) -> None:
        with pytest.raises(ValidationError):
            PtyResizeMessage(type=PtyInputMessageType.RESIZE, rows=24, cols=80, extra="bad")  # type: ignore[call-arg]


class TestPtyPingMessage:
    def test_valid(self) -> None:
        msg = PtyPingMessage(type=PtyInputMessageType.PING)
        assert msg.type == PtyInputMessageType.PING

    def test_rejects_extra_fields(self) -> None:
        with pytest.raises(ValidationError):
            PtyPingMessage(type=PtyInputMessageType.PING, extra="bad")  # type: ignore[call-arg]


class TestPtyRestartMessage:
    def test_valid(self) -> None:
        msg = PtyRestartMessage(type=PtyInputMessageType.RESTART)
        assert msg.type == PtyInputMessageType.RESTART


class TestPtyClientMessageDiscriminatedUnion:
    def test_stdin_dispatch(self) -> None:
        msg = _pty_client_adapter.validate_python({"type": "stdin", "chars": "abc"})
        assert isinstance(msg, PtyStdinMessage)

    def test_resize_dispatch(self) -> None:
        msg = _pty_client_adapter.validate_python({"type": "resize", "rows": 24, "cols": 80})
        assert isinstance(msg, PtyResizeMessage)

    def test_ping_dispatch(self) -> None:
        msg = _pty_client_adapter.validate_python({"type": "ping"})
        assert isinstance(msg, PtyPingMessage)

    def test_restart_dispatch(self) -> None:
        msg = _pty_client_adapter.validate_python({"type": "restart"})
        assert isinstance(msg, PtyRestartMessage)

    def test_invalid_type(self) -> None:
        with pytest.raises(ValidationError):
            _pty_client_adapter.validate_python({"type": "unknown"})


class TestPtyOutputMessage:
    def test_valid(self) -> None:
        msg = PtyOutputMessage(type=PtyOutputMessageType.OUT, data="aGVsbG8=")
        assert msg.type == PtyOutputMessageType.OUT
        assert msg.data == "aGVsbG8="

    def test_missing_data(self) -> None:
        with pytest.raises(ValidationError):
            PtyOutputMessage(type=PtyOutputMessageType.OUT)  # type: ignore[call-arg]


# ============================
# Execute WebSocket Message Tests
# ============================


class TestExecuteRequest:
    def test_valid_with_defaults(self) -> None:
        req = ExecuteRequest(mode=ExecuteMode.QUERY)
        assert req.mode == ExecuteMode.QUERY
        assert req.code == ""
        assert req.options == {}

    def test_valid_with_all_fields(self) -> None:
        req = ExecuteRequest(mode=ExecuteMode.BATCH, code="print('hi')", options={"flag": True})
        assert req.mode == ExecuteMode.BATCH
        assert req.code == "print('hi')"
        assert req.options == {"flag": True}

    def test_missing_mode(self) -> None:
        with pytest.raises(ValidationError):
            ExecuteRequest()  # type: ignore[call-arg]

    def test_invalid_mode(self) -> None:
        with pytest.raises(ValidationError):
            ExecuteRequest(mode="invalid")  # type: ignore[arg-type]

    def test_rejects_extra_fields(self) -> None:
        with pytest.raises(ValidationError):
            ExecuteRequest(mode=ExecuteMode.QUERY, extra="bad")  # type: ignore[call-arg]


class TestExecuteResult:
    def test_valid_finished(self) -> None:
        result = ExecuteResult(status="finished", exitCode=0)
        assert result.status == "finished"
        assert result.exitCode == 0
        assert result.console is None
        assert result.options is None
        assert result.files is None
        assert result.msg is None

    def test_valid_error(self) -> None:
        result = ExecuteResult(status="error", msg="something went wrong")
        assert result.status == "error"
        assert result.msg == "something went wrong"

    def test_valid_with_console(self) -> None:
        result = ExecuteResult(status="finished", console=[["stdout", "hello\n"]])
        assert result.console == [["stdout", "hello\n"]]

    def test_missing_status(self) -> None:
        with pytest.raises(ValidationError):
            ExecuteResult()  # type: ignore[call-arg]

    def test_rejects_extra_fields(self) -> None:
        with pytest.raises(ValidationError):
            ExecuteResult(status="finished", extra="bad")  # type: ignore[call-arg]


# ============================
# Proxy / App Parameter Tests
# ============================


class TestStreamProxyParams:
    def test_valid_minimal(self) -> None:
        params = StreamProxyParams(app="jupyter")
        assert params.app == "jupyter"
        assert params.port is None
        assert params.envs is None
        assert params.arguments is None

    def test_valid_with_all_fields(self) -> None:
        params = StreamProxyParams(
            app="ttyd",
            port=8080,
            envs='{"PASSWORD": "123"}',
            arguments='{"-P": "123"}',
        )
        assert params.app == "ttyd"
        assert params.port == 8080

    def test_service_alias(self) -> None:
        params = StreamProxyParams.model_validate({"service": "jupyter"})
        assert params.app == "jupyter"

    def test_port_min_boundary(self) -> None:
        params = StreamProxyParams(app="test", port=1024)
        assert params.port == 1024

    def test_port_max_boundary(self) -> None:
        params = StreamProxyParams(app="test", port=65535)
        assert params.port == 65535

    def test_port_below_min(self) -> None:
        with pytest.raises(ValidationError):
            StreamProxyParams(app="test", port=1023)

    def test_port_above_max(self) -> None:
        with pytest.raises(ValidationError):
            StreamProxyParams(app="test", port=65536)

    def test_missing_app(self) -> None:
        with pytest.raises(ValidationError):
            StreamProxyParams()  # type: ignore[call-arg]

    def test_rejects_extra_fields(self) -> None:
        with pytest.raises(ValidationError):
            StreamProxyParams(app="test", extra="bad")  # type: ignore[call-arg]


class TestStreamAppInfo:
    def test_valid_minimal(self) -> None:
        info = StreamAppInfo(name="jupyter", protocol="http", ports=[8080])
        assert info.name == "jupyter"
        assert info.protocol == "http"
        assert info.ports == [8080]
        assert info.url_template is None
        assert info.allowed_arguments is None
        assert info.allowed_envs is None

    def test_valid_with_optional_fields(self) -> None:
        info = StreamAppInfo(
            name="ttyd",
            protocol="http",
            ports=[7681, 7682],
            url_template="http://localhost:{port}",
            allowed_arguments={"-P": "password"},
            allowed_envs={"PASSWORD": "string"},
        )
        assert info.ports == [7681, 7682]
        assert info.url_template == "http://localhost:{port}"

    def test_missing_required_field(self) -> None:
        with pytest.raises(ValidationError):
            StreamAppInfo(name="test", protocol="http")  # type: ignore[call-arg]


# ============================
# SSE Event Parameter Tests
# ============================


class TestSessionEventParams:
    def test_defaults(self) -> None:
        params = SessionEventParams()
        assert params.session_name == "*"
        assert params.owner_access_key is None
        assert params.session_id is None
        assert params.group_name == "*"
        assert params.scope == "*"

    def test_alias_name(self) -> None:
        params = SessionEventParams.model_validate({"name": "my-session"})
        assert params.session_name == "my-session"

    def test_alias_session_name_camel(self) -> None:
        params = SessionEventParams.model_validate({"sessionName": "my-session"})
        assert params.session_name == "my-session"

    def test_alias_owner_access_key(self) -> None:
        params = SessionEventParams.model_validate({"ownerAccessKey": "AKTEST"})
        assert params.owner_access_key == "AKTEST"

    def test_alias_session_id(self) -> None:
        uid = uuid4()
        params = SessionEventParams.model_validate({"sessionId": str(uid)})
        assert params.session_id == uid

    def test_alias_group(self) -> None:
        params = SessionEventParams.model_validate({"group": "my-group"})
        assert params.group_name == "my-group"

    def test_alias_group_name_camel(self) -> None:
        params = SessionEventParams.model_validate({"groupName": "my-group"})
        assert params.group_name == "my-group"

    def test_rejects_extra_fields(self) -> None:
        with pytest.raises(ValidationError):
            SessionEventParams.model_validate({"extra": "bad"})


class TestBackgroundTaskEventParams:
    def test_valid(self) -> None:
        uid = uuid4()
        params = BackgroundTaskEventParams(task_id=uid)
        assert params.task_id == uid

    def test_alias_task_id_camel(self) -> None:
        uid = uuid4()
        params = BackgroundTaskEventParams.model_validate({"taskId": str(uid)})
        assert params.task_id == uid

    def test_missing_task_id(self) -> None:
        with pytest.raises(ValidationError):
            BackgroundTaskEventParams()  # type: ignore[call-arg]

    def test_invalid_uuid(self) -> None:
        with pytest.raises(ValidationError):
            BackgroundTaskEventParams.model_validate({"task_id": "not-a-uuid"})


# ============================
# SSE Event Payload Tests
# ============================


class TestBgtaskUpdatedPayload:
    def test_valid(self) -> None:
        payload = BgtaskUpdatedPayload(
            task_id="abc123",
            message="Processing...",
            current_progress=50.0,
            total_progress=100.0,
        )
        assert payload.task_id == "abc123"
        assert payload.current_progress == 50.0
        assert payload.total_progress == 100.0

    def test_missing_required(self) -> None:
        with pytest.raises(ValidationError):
            BgtaskUpdatedPayload(task_id="abc", message="test")  # type: ignore[call-arg]

    def test_round_trip(self) -> None:
        data = {
            "task_id": "abc123",
            "message": "ok",
            "current_progress": 0.5,
            "total_progress": 1.0,
        }
        payload = BgtaskUpdatedPayload.model_validate(data)
        dumped = payload.model_dump()
        assert dumped == data


class TestBgtaskDonePayload:
    def test_valid(self) -> None:
        payload = BgtaskDonePayload(task_id="abc123", message="Done!")
        assert payload.task_id == "abc123"
        assert payload.message == "Done!"

    def test_round_trip(self) -> None:
        data = {"task_id": "t1", "message": "completed"}
        payload = BgtaskDonePayload.model_validate(data)
        assert payload.model_dump() == data


class TestBgtaskPartialSuccessPayload:
    def test_valid(self) -> None:
        payload = BgtaskPartialSuccessPayload(
            task_id="abc", message="partial", errors=["err1", "err2"]
        )
        assert payload.errors == ["err1", "err2"]

    def test_missing_errors(self) -> None:
        with pytest.raises(ValidationError):
            BgtaskPartialSuccessPayload(task_id="abc", message="partial")  # type: ignore[call-arg]


class TestBgtaskCancelledPayload:
    def test_valid(self) -> None:
        payload = BgtaskCancelledPayload(task_id="abc", message="Cancelled")
        assert payload.task_id == "abc"

    def test_rejects_extra_fields(self) -> None:
        with pytest.raises(ValidationError):
            BgtaskCancelledPayload(
                task_id="abc",
                message="cancelled",
                extra="bad",  # type: ignore[call-arg]
            )


class TestBgtaskFailedPayload:
    def test_valid(self) -> None:
        payload = BgtaskFailedPayload(task_id="abc", message="Failed")
        assert payload.task_id == "abc"

    def test_round_trip(self) -> None:
        data = {"task_id": "f1", "message": "failed"}
        payload = BgtaskFailedPayload.model_validate(data)
        assert payload.model_dump() == data
