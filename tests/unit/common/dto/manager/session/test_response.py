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
        resp = CreateSessionResponse()
        assert resp.result == {}

    def test_with_data(self) -> None:
        resp = CreateSessionResponse.model_validate({
            "result": {"sessionId": str(uuid4()), "status": "PENDING"},
        })
        assert "sessionId" in resp.result

    def test_json_serialization(self) -> None:
        resp = CreateSessionResponse(result={"key": "value"})
        data = resp.model_dump(mode="json")
        assert data["result"] == {"key": "value"}


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
        resp = GetCommitStatusResponse()
        assert resp.result == {}


class TestGetAbusingReportResponse:
    def test_empty(self) -> None:
        resp = GetAbusingReportResponse()
        assert resp.result == {}


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


class TestCommitSessionResponse:
    def test_with_result(self) -> None:
        resp = CommitSessionResponse(result={"commit_id": "abc"})
        assert resp.result["commit_id"] == "abc"


class TestConvertSessionToImageResponse:
    def test_task_id(self) -> None:
        resp = ConvertSessionToImageResponse(task_id="task-001")
        assert resp.task_id == "task-001"


class TestDestroySessionResponse:
    def test_empty(self) -> None:
        resp = DestroySessionResponse()
        assert resp.result == {}


class TestGetSessionInfoResponse:
    def test_with_info(self) -> None:
        resp = GetSessionInfoResponse(result={"name": "sess", "status": "RUNNING"})
        assert resp.result["name"] == "sess"


class TestGetDirectAccessInfoResponse:
    def test_empty(self) -> None:
        resp = GetDirectAccessInfoResponse()
        assert resp.result == {}


class TestMatchSessionsResponse:
    def test_empty(self) -> None:
        resp = MatchSessionsResponse()
        assert resp.matches == []

    def test_with_matches(self) -> None:
        resp = MatchSessionsResponse(matches=["sess-1", "sess-2"])
        assert len(resp.matches) == 2


class TestExecuteResponse:
    def test_with_result(self) -> None:
        resp = ExecuteResponse(result={"status": "finished"})
        assert resp.result["status"] == "finished"


class TestCompleteResponse:
    def test_empty(self) -> None:
        resp = CompleteResponse()
        assert resp.result == {}


class TestListFilesResponse:
    def test_with_result(self) -> None:
        resp = ListFilesResponse(result={"files": ["a.txt"]})
        assert resp.result["files"] == ["a.txt"]


class TestGetContainerLogsResponse:
    def test_with_result(self) -> None:
        resp = GetContainerLogsResponse(result={"log": "hello world"})
        assert resp.result["log"] == "hello world"


class TestGetStatusHistoryResponse:
    def test_with_result(self) -> None:
        resp = GetStatusHistoryResponse(result={"RUNNING": "2025-01-01"})
        assert "RUNNING" in resp.result


class TestGetDependencyGraphResponse:
    def test_empty(self) -> None:
        resp = GetDependencyGraphResponse()
        assert resp.result == {}
