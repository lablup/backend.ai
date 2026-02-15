"""Unit tests for SessionClient (SDK v2)."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from yarl import URL

from ai.backend.client.v2.base_client import BackendAIClient
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.domains.session import SessionClient
from ai.backend.common.dto.manager.session.request import (
    CommitSessionRequest,
    CompleteRequest,
    ConvertSessionToImageRequest,
    CreateClusterRequest,
    CreateFromParamsRequest,
    CreateFromTemplateRequest,
    DestroySessionRequest,
    DownloadFilesRequest,
    DownloadSingleRequest,
    ExecuteRequest,
    GetTaskLogsRequest,
    ListFilesRequest,
    MatchSessionsRequest,
    RenameSessionRequest,
    ShutdownServiceRequest,
    StartServiceRequest,
    SyncAgentRegistryRequest,
    TransitSessionStatusRequest,
)
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

from .conftest import MockAuth

_DEFAULT_CONFIG = ClientConfig(endpoint=URL("https://api.example.com"))


def _make_request_session(resp: AsyncMock) -> MagicMock:
    """Build a mock aiohttp session whose ``request()`` returns *resp*."""
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=resp)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)

    mock_session = MagicMock()
    mock_session.request = MagicMock(return_value=mock_ctx)
    return mock_session


def _json_response(data: dict[str, Any], *, status: int = 200) -> AsyncMock:
    resp = AsyncMock()
    resp.status = status
    resp.json = AsyncMock(return_value=data)
    return resp


def _no_content_response() -> AsyncMock:
    resp = AsyncMock()
    resp.status = 204
    return resp


def _make_session_client(mock_session: MagicMock) -> SessionClient:
    client = BackendAIClient(_DEFAULT_CONFIG, MockAuth(), mock_session)
    return SessionClient(client)


def _last_request_call(mock_session: MagicMock) -> tuple[str, str, dict[str, Any] | None]:
    """Return (method, url, json_body) from the last ``session.request()`` call."""
    args, kwargs = mock_session.request.call_args
    return args[0], str(args[1]), kwargs.get("json")


# ---------------------------------------------------------------------------
# Session creation
# ---------------------------------------------------------------------------


class TestSessionCreation:
    @pytest.mark.asyncio
    async def test_create_from_params(self) -> None:
        resp = _json_response({"result": {"session_id": "abc"}})
        mock_session = _make_request_session(resp)
        sc = _make_session_client(mock_session)

        result = await sc.create_from_params(
            CreateFromParamsRequest(session_name="my-sess", image="python:3.11")
        )

        assert isinstance(result, CreateSessionResponse)
        method, url, body = _last_request_call(mock_session)
        assert method == "POST"
        assert url.endswith("/session")
        assert body is not None
        assert body["session_name"] == "my-sess"

    @pytest.mark.asyncio
    async def test_create_from_template(self) -> None:
        template_id = uuid4()
        resp = _json_response({"result": {"session_id": "xyz"}})
        mock_session = _make_request_session(resp)
        sc = _make_session_client(mock_session)

        result = await sc.create_from_template(CreateFromTemplateRequest(template_id=template_id))

        assert isinstance(result, CreateSessionResponse)
        method, url, _ = _last_request_call(mock_session)
        assert method == "POST"
        assert url.endswith("/session/_/create-from-template")

    @pytest.mark.asyncio
    async def test_create_cluster(self) -> None:
        template_id = uuid4()
        resp = _json_response({"result": {"session_id": "cls"}})
        mock_session = _make_request_session(resp)
        sc = _make_session_client(mock_session)

        result = await sc.create_cluster(
            CreateClusterRequest(session_name="cluster-1", template_id=template_id)
        )

        assert isinstance(result, CreateSessionResponse)
        method, url, _ = _last_request_call(mock_session)
        assert method == "POST"
        assert url.endswith("/session/_/create-cluster")


# ---------------------------------------------------------------------------
# Session lifecycle
# ---------------------------------------------------------------------------


class TestSessionLifecycle:
    @pytest.mark.asyncio
    async def test_get_info(self) -> None:
        resp = _json_response({"result": {"id": "s-123", "status": "RUNNING"}})
        mock_session = _make_request_session(resp)
        sc = _make_session_client(mock_session)

        result = await sc.get_info("my-sess")

        assert isinstance(result, GetSessionInfoResponse)
        method, url, _ = _last_request_call(mock_session)
        assert method == "GET"
        assert "/session/my-sess" in url

    @pytest.mark.asyncio
    async def test_get_info_with_owner_access_key(self) -> None:
        resp = _json_response({"result": {"id": "s-123"}})
        mock_session = _make_request_session(resp)
        sc = _make_session_client(mock_session)

        await sc.get_info("my-sess", owner_access_key="AKID1234")

        _, _, _ = _last_request_call(mock_session)
        call_kwargs = mock_session.request.call_args.kwargs
        assert call_kwargs["params"] == {"owner_access_key": "AKID1234"}

    @pytest.mark.asyncio
    async def test_destroy(self) -> None:
        resp = _json_response({"result": {"status": "TERMINATED"}})
        mock_session = _make_request_session(resp)
        sc = _make_session_client(mock_session)

        result = await sc.destroy("my-sess", DestroySessionRequest(forced=True))

        assert isinstance(result, DestroySessionResponse)
        method, url, body = _last_request_call(mock_session)
        assert method == "DELETE"
        assert "/session/my-sess" in url
        assert body is not None
        assert body["forced"] is True

    @pytest.mark.asyncio
    async def test_restart(self) -> None:
        resp = _no_content_response()
        mock_session = _make_request_session(resp)
        sc = _make_session_client(mock_session)

        await sc.restart("my-sess")

        method, url, _ = _last_request_call(mock_session)
        assert method == "PATCH"
        assert "/session/my-sess" in url

    @pytest.mark.asyncio
    async def test_rename(self) -> None:
        resp = _no_content_response()
        mock_session = _make_request_session(resp)
        sc = _make_session_client(mock_session)

        await sc.rename("old-name", RenameSessionRequest(session_name="new-name"))

        method, url, body = _last_request_call(mock_session)
        assert method == "POST"
        assert "/session/old-name/rename" in url
        assert body is not None
        assert body["session_name"] == "new-name"

    @pytest.mark.asyncio
    async def test_interrupt(self) -> None:
        resp = _no_content_response()
        mock_session = _make_request_session(resp)
        sc = _make_session_client(mock_session)

        await sc.interrupt("my-sess")

        method, url, _ = _last_request_call(mock_session)
        assert method == "POST"
        assert "/session/my-sess/interrupt" in url

    @pytest.mark.asyncio
    async def test_match_sessions(self) -> None:
        resp = _json_response({"matches": [{"id": "s1"}, {"id": "s2"}]})
        mock_session = _make_request_session(resp)
        sc = _make_session_client(mock_session)

        result = await sc.match_sessions(MatchSessionsRequest(id="prefix"))

        assert isinstance(result, MatchSessionsResponse)
        assert len(result.matches) == 2
        method, url, _ = _last_request_call(mock_session)
        assert method == "GET"
        assert "/session/_/match" in url


# ---------------------------------------------------------------------------
# Code execution
# ---------------------------------------------------------------------------


class TestCodeExecution:
    @pytest.mark.asyncio
    async def test_execute(self) -> None:
        resp = _json_response({"result": {"status": "finished", "console": []}})
        mock_session = _make_request_session(resp)
        sc = _make_session_client(mock_session)

        result = await sc.execute("my-sess", ExecuteRequest(mode="query", code="print(1)"))

        assert isinstance(result, ExecuteResponse)
        method, url, body = _last_request_call(mock_session)
        assert method == "POST"
        assert url.endswith("/session/my-sess")
        assert body is not None
        assert body["code"] == "print(1)"

    @pytest.mark.asyncio
    async def test_complete(self) -> None:
        resp = _json_response({"result": {"candidates": ["print"]}})
        mock_session = _make_request_session(resp)
        sc = _make_session_client(mock_session)

        result = await sc.complete("my-sess", CompleteRequest(code="pri"))

        assert isinstance(result, CompleteResponse)
        method, url, _ = _last_request_call(mock_session)
        assert method == "POST"
        assert "/session/my-sess/complete" in url


# ---------------------------------------------------------------------------
# Services
# ---------------------------------------------------------------------------


class TestServices:
    @pytest.mark.asyncio
    async def test_start_service(self) -> None:
        resp = _json_response({"token": "tok-123", "wsproxy_addr": "ws://proxy:5050"})
        mock_session = _make_request_session(resp)
        sc = _make_session_client(mock_session)

        result = await sc.start_service("my-sess", StartServiceRequest(app="jupyter"))

        assert isinstance(result, StartServiceResponse)
        assert result.token == "tok-123"
        method, url, _ = _last_request_call(mock_session)
        assert method == "POST"
        assert "/session/my-sess/start-service" in url

    @pytest.mark.asyncio
    async def test_shutdown_service(self) -> None:
        resp = _no_content_response()
        mock_session = _make_request_session(resp)
        sc = _make_session_client(mock_session)

        await sc.shutdown_service("my-sess", ShutdownServiceRequest(service_name="jupyter"))

        method, url, body = _last_request_call(mock_session)
        assert method == "POST"
        assert "/session/my-sess/shutdown-service" in url
        assert body is not None
        assert body["service_name"] == "jupyter"


# ---------------------------------------------------------------------------
# Commit / imagify
# ---------------------------------------------------------------------------


class TestCommitAndImage:
    @pytest.mark.asyncio
    async def test_commit(self) -> None:
        resp = _json_response({"result": {"task_id": "t-1"}})
        mock_session = _make_request_session(resp)
        sc = _make_session_client(mock_session)

        result = await sc.commit("my-sess", CommitSessionRequest())

        assert isinstance(result, CommitSessionResponse)
        method, url, _ = _last_request_call(mock_session)
        assert method == "POST"
        assert "/session/my-sess/commit" in url

    @pytest.mark.asyncio
    async def test_get_commit_status(self) -> None:
        resp = _json_response({"result": {"status": "ongoing"}})
        mock_session = _make_request_session(resp)
        sc = _make_session_client(mock_session)

        result = await sc.get_commit_status("my-sess")

        assert isinstance(result, GetCommitStatusResponse)
        method, url, _ = _last_request_call(mock_session)
        assert method == "GET"
        assert "/session/my-sess/commit" in url

    @pytest.mark.asyncio
    async def test_convert_to_image(self) -> None:
        resp = _json_response({"task_id": "task-abc"})
        mock_session = _make_request_session(resp)
        sc = _make_session_client(mock_session)

        result = await sc.convert_to_image(
            "my-sess",
            ConvertSessionToImageRequest(image_name="my-custom-img"),
        )

        assert isinstance(result, ConvertSessionToImageResponse)
        assert result.task_id == "task-abc"
        method, url, _ = _last_request_call(mock_session)
        assert method == "POST"
        assert "/session/my-sess/imagify" in url


# ---------------------------------------------------------------------------
# Files & logs
# ---------------------------------------------------------------------------


class TestFilesAndLogs:
    @pytest.mark.asyncio
    async def test_list_files(self) -> None:
        resp = _json_response({"result": {"files": []}})
        mock_session = _make_request_session(resp)
        sc = _make_session_client(mock_session)

        result = await sc.list_files("my-sess", ListFilesRequest(path="/home"))

        assert isinstance(result, ListFilesResponse)
        method, url, _ = _last_request_call(mock_session)
        assert method == "GET"
        assert "/session/my-sess/files" in url

    @pytest.mark.asyncio
    async def test_get_container_logs(self) -> None:
        resp = _json_response({"result": {"logs": "hello\n"}})
        mock_session = _make_request_session(resp)
        sc = _make_session_client(mock_session)

        result = await sc.get_container_logs("my-sess")

        assert isinstance(result, GetContainerLogsResponse)
        method, url, _ = _last_request_call(mock_session)
        assert method == "GET"
        assert "/session/my-sess/logs" in url

    @pytest.mark.asyncio
    async def test_get_status_history(self) -> None:
        resp = _json_response({"result": {"history": []}})
        mock_session = _make_request_session(resp)
        sc = _make_session_client(mock_session)

        result = await sc.get_status_history("my-sess")

        assert isinstance(result, GetStatusHistoryResponse)
        method, url, _ = _last_request_call(mock_session)
        assert method == "GET"
        assert "/session/my-sess/status-history" in url


# ---------------------------------------------------------------------------
# Matching & Admin
# ---------------------------------------------------------------------------


class TestMatchingAndAdmin:
    @pytest.mark.asyncio
    async def test_sync_agent_registry(self) -> None:
        resp = _json_response({"synced": True})
        mock_session = _make_request_session(resp)
        sc = _make_session_client(mock_session)

        result = await sc.sync_agent_registry(SyncAgentRegistryRequest(agent="agent-001"))

        assert isinstance(result, dict)
        assert result["synced"] is True
        method, url, body = _last_request_call(mock_session)
        assert method == "POST"
        assert "/session/_/sync-agent-registry" in url
        assert body is not None
        assert body["agent"] == "agent-001"

    @pytest.mark.asyncio
    async def test_transit_session_status(self) -> None:
        sid = uuid4()
        resp = _json_response({"session_status_map": {str(sid): "RUNNING"}})
        mock_session = _make_request_session(resp)
        sc = _make_session_client(mock_session)

        result = await sc.transit_session_status(TransitSessionStatusRequest(ids=[sid]))

        assert isinstance(result, TransitSessionStatusResponse)
        method, url, _ = _last_request_call(mock_session)
        assert method == "POST"
        assert "/session/_/transit-status" in url


# ---------------------------------------------------------------------------
# Other endpoints
# ---------------------------------------------------------------------------


class TestOtherEndpoints:
    @pytest.mark.asyncio
    async def test_get_direct_access_info(self) -> None:
        resp = _json_response({"result": {"host": "10.0.0.1"}})
        mock_session = _make_request_session(resp)
        sc = _make_session_client(mock_session)

        result = await sc.get_direct_access_info("my-sess")

        assert isinstance(result, GetDirectAccessInfoResponse)
        method, url, _ = _last_request_call(mock_session)
        assert method == "GET"
        assert "/session/my-sess/direct-access-info" in url

    @pytest.mark.asyncio
    async def test_get_dependency_graph(self) -> None:
        resp = _json_response({"result": {"nodes": [], "edges": []}})
        mock_session = _make_request_session(resp)
        sc = _make_session_client(mock_session)

        result = await sc.get_dependency_graph("my-sess")

        assert isinstance(result, GetDependencyGraphResponse)
        method, url, _ = _last_request_call(mock_session)
        assert method == "GET"
        assert "/session/my-sess/dependency-graph" in url

    @pytest.mark.asyncio
    async def test_get_abusing_report(self) -> None:
        resp = _json_response({"result": {"abuse_count": 0}})
        mock_session = _make_request_session(resp)
        sc = _make_session_client(mock_session)

        result = await sc.get_abusing_report("my-sess")

        assert isinstance(result, GetAbusingReportResponse)
        method, url, _ = _last_request_call(mock_session)
        assert method == "GET"
        assert "/session/my-sess/abusing-report" in url


# ---------------------------------------------------------------------------
# Binary / multipart operations
# ---------------------------------------------------------------------------


class TestBinaryOperations:
    @pytest.mark.asyncio
    async def test_upload_files(self, tmp_path: Any) -> None:
        test_file = tmp_path / "hello.txt"
        test_file.write_bytes(b"hello world")

        mock_client = BackendAIClient(_DEFAULT_CONFIG, MockAuth(), MagicMock())
        sc = SessionClient(mock_client)
        mock_upload = AsyncMock(return_value={"uploaded": True})

        with patch.object(mock_client, "upload", mock_upload):
            result = await sc.upload_files("my-sess", [str(test_file)], basedir=str(tmp_path))

        assert result == {"uploaded": True}
        mock_upload.assert_awaited_once()
        call_args = mock_upload.call_args
        assert "/session/my-sess/upload" in call_args.args[0]

    @pytest.mark.asyncio
    async def test_download_files(self) -> None:
        mock_client = BackendAIClient(_DEFAULT_CONFIG, MockAuth(), MagicMock())
        sc = SessionClient(mock_client)
        mock_download = AsyncMock(return_value=b"zip-content")

        with patch.object(mock_client, "download", mock_download):
            result = await sc.download_files(
                "my-sess", DownloadFilesRequest(files=["a.txt", "b.txt"])
            )

        assert result == b"zip-content"
        mock_download.assert_awaited_once()
        call_args = mock_download.call_args
        assert "/session/my-sess/download" in call_args.args[0]
        assert call_args.kwargs["json"]["files"] == ["a.txt", "b.txt"]

    @pytest.mark.asyncio
    async def test_download_single(self) -> None:
        mock_client = BackendAIClient(_DEFAULT_CONFIG, MockAuth(), MagicMock())
        sc = SessionClient(mock_client)
        mock_download = AsyncMock(return_value=b"file-bytes")

        with patch.object(mock_client, "download", mock_download):
            result = await sc.download_single("my-sess", DownloadSingleRequest(file="data.csv"))

        assert result == b"file-bytes"
        mock_download.assert_awaited_once()
        call_args = mock_download.call_args
        assert "/session/my-sess/download_single" in call_args.args[0]
        assert call_args.kwargs["json"]["file"] == "data.csv"

    @pytest.mark.asyncio
    async def test_get_task_logs(self) -> None:
        kernel_id = uuid4()
        mock_client = BackendAIClient(_DEFAULT_CONFIG, MockAuth(), MagicMock())
        sc = SessionClient(mock_client)
        mock_download = AsyncMock(return_value=b"log-output")

        with patch.object(mock_client, "download", mock_download):
            result = await sc.get_task_logs(GetTaskLogsRequest(kernel_id=kernel_id))

        assert result == b"log-output"
        mock_download.assert_awaited_once()
        call_args = mock_download.call_args
        assert "/session/_/logs" in call_args.args[0]
        assert call_args.kwargs["method"] == "GET"
        assert call_args.kwargs["params"]["taskId"] == str(kernel_id)
