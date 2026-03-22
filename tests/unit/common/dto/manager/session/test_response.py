from __future__ import annotations

from uuid import uuid4

from ai.backend.common.dto.manager.session.response import (
    CommitSessionResponse,
    CompleteResponse,
    ConvertSessionToImageResponse,
    CreateSessionResponse,
    DestroySessionResponse,
    ExecuteResponse,
    GetAbusingReportResponse,
    GetCommitStatusResponse,
    GetContainerLogsResponse,
    GetDependencyGraphResponse,
    GetDirectAccessInfoResponse,
    GetSessionInfoResponse,
    GetStatusHistoryResponse,
    ListFilesResponse,
    MatchSessionsResponse,
    StartServiceResponse,
    TransitSessionStatusResponse,
)
from ai.backend.common.types import SessionId


class TestCreateSessionResponse:
    def test_empty_result(self) -> None:
        resp = CreateSessionResponse({})
        assert resp.root == {}

    def test_with_data(self) -> None:
        resp = CreateSessionResponse.model_validate({
            "sessionId": str(uuid4()),
            "status": "PENDING",
        })
        assert "sessionId" in resp.root

    def test_json_serialization(self) -> None:
        resp = CreateSessionResponse({"key": "value"})
        data = resp.model_dump(mode="json")
        assert data == {"key": "value"}


class TestStartServiceResponse:
    def test_fields(self) -> None:
        resp = StartServiceResponse(token="abc123", wsproxy_addr="ws://localhost:5050")
        assert resp.token == "abc123"
        assert resp.wsproxy_addr == "ws://localhost:5050"

    def test_json_serialization(self) -> None:
        resp = StartServiceResponse(token="t", wsproxy_addr="w")
        data = resp.model_dump(mode="json")
        assert data["token"] == "t"
        assert data["wsproxy_addr"] == "w"


class TestGetCommitStatusResponse:
    def test_empty(self) -> None:
        resp = GetCommitStatusResponse({})
        assert resp.root == {}


class TestGetAbusingReportResponse:
    def test_empty(self) -> None:
        resp = GetAbusingReportResponse({})
        assert resp.root == {}


class TestTransitSessionStatusResponse:
    def test_with_map(self) -> None:
        sid = SessionId(uuid4())
        resp = TransitSessionStatusResponse(session_status_map={sid: "RUNNING"})
        assert resp.session_status_map[sid] == "RUNNING"

    def test_json_serialization(self) -> None:
        sid = SessionId(uuid4())
        resp = TransitSessionStatusResponse(session_status_map={sid: "TERMINATED"})
        data = resp.model_dump(mode="json")
        assert str(sid) in data["session_status_map"]

    def test_json_deserialization_string_keys(self) -> None:
        """Verify that string UUID keys are correctly converted to SessionId
        during JSON round-trip deserialization."""
        sid = uuid4()
        raw = {"session_status_map": {str(sid): "RUNNING"}}
        resp = TransitSessionStatusResponse.model_validate(raw)
        assert SessionId(sid) in resp.session_status_map
        assert resp.session_status_map[SessionId(sid)] == "RUNNING"

    def test_json_round_trip(self) -> None:
        """Ensure dump → validate round-trip preserves SessionId keys."""
        sid = SessionId(uuid4())
        original = TransitSessionStatusResponse(session_status_map={sid: "PENDING"})
        dumped = original.model_dump(mode="json")
        restored = TransitSessionStatusResponse.model_validate(dumped)
        assert restored.session_status_map[sid] == "PENDING"


class TestCommitSessionResponse:
    def test_with_result(self) -> None:
        resp = CommitSessionResponse({"commit_id": "abc"})
        assert resp.root["commit_id"] == "abc"


class TestConvertSessionToImageResponse:
    def test_task_id(self) -> None:
        resp = ConvertSessionToImageResponse(task_id="task-001")
        assert resp.task_id == "task-001"


class TestDestroySessionResponse:
    def test_empty(self) -> None:
        resp = DestroySessionResponse({})
        assert resp.root == {}


class TestGetSessionInfoResponse:
    def test_with_info(self) -> None:
        resp = GetSessionInfoResponse.model_validate({"status": "RUNNING", "domainName": "default"})
        assert resp.root["status"] == "RUNNING"
        assert resp.root["domainName"] == "default"


class TestGetDirectAccessInfoResponse:
    def test_empty(self) -> None:
        resp = GetDirectAccessInfoResponse({})
        assert resp.root == {}


class TestMatchSessionsResponse:
    def test_empty(self) -> None:
        resp = MatchSessionsResponse()
        assert resp.matches == []

    def test_with_matches(self) -> None:
        resp = MatchSessionsResponse(matches=["sess-1", "sess-2"])
        assert len(resp.matches) == 2


class TestExecuteResponse:
    def test_with_result(self) -> None:
        resp = ExecuteResponse({"status": "finished"})
        assert resp.root["status"] == "finished"


class TestCompleteResponse:
    def test_empty(self) -> None:
        resp = CompleteResponse({})
        assert resp.root == {}


class TestListFilesResponse:
    def test_with_result(self) -> None:
        resp = ListFilesResponse({"files": ["a.txt"]})
        assert resp.root["files"] == ["a.txt"]


class TestGetContainerLogsResponse:
    def test_with_result(self) -> None:
        resp = GetContainerLogsResponse({"log": "hello world"})
        assert resp.root["log"] == "hello world"


class TestGetStatusHistoryResponse:
    def test_with_result(self) -> None:
        resp = GetStatusHistoryResponse({"RUNNING": "2025-01-01"})
        assert "RUNNING" in resp.root


class TestGetDependencyGraphResponse:
    def test_empty(self) -> None:
        resp = GetDependencyGraphResponse({})
        assert resp.root == {}
