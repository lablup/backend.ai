from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from yarl import URL

from ai.backend.client.v2.base_client import BackendAIClient
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.domains.operations import OperationsClient
from ai.backend.common.dto.manager.operations import (
    AppendErrorLogRequest,
    AppendErrorLogResponse,
    ClearErrorLogResponse,
    FetchManagerStatusResponse,
    GetAnnouncementResponse,
    ListErrorLogsRequest,
    ListErrorLogsResponse,
    PerformSchedulerOpsRequest,
    UpdateAnnouncementRequest,
    UpdateManagerStatusRequest,
)
from ai.backend.common.dto.manager.operations.types import (
    ErrorLogSeverity,
    ManagerStatus,
    SchedulerOps,
)

from .conftest import MockAuth

_DEFAULT_CONFIG = ClientConfig(endpoint=URL("https://api.example.com"))


def _make_request_session(resp: AsyncMock) -> MagicMock:
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=resp)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)
    mock_session = MagicMock()
    mock_session.request = MagicMock(return_value=mock_ctx)
    return mock_session


def _make_client(mock_session: MagicMock) -> BackendAIClient:
    return BackendAIClient(_DEFAULT_CONFIG, MockAuth(), mock_session)


def _make_ops_client(mock_session: MagicMock) -> OperationsClient:
    return OperationsClient(_make_client(mock_session))


class TestAppendErrorLog:
    @pytest.mark.asyncio
    async def test_sends_post_with_body(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={"success": True})
        mock_session = _make_request_session(mock_resp)
        client = _make_ops_client(mock_session)

        request = AppendErrorLogRequest(
            severity=ErrorLogSeverity.ERROR,
            source="manager",
            message="test error",
            context_lang="python",
            context_env='{"key": "val"}',
        )
        result = await client.append_error_log(request)

        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
        assert "/logs/error" in str(call_args[0][1])
        assert isinstance(result, AppendErrorLogResponse)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_serializes_all_fields(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={"success": True})
        mock_session = _make_request_session(mock_resp)
        client = _make_ops_client(mock_session)

        request = AppendErrorLogRequest(
            severity=ErrorLogSeverity.CRITICAL,
            source="agent",
            message="critical failure",
            context_lang="python",
            context_env="{}",
            request_url="/api/test",
            request_status=500,
            traceback="Traceback ...",
        )
        await client.append_error_log(request)

        call_kwargs = mock_session.request.call_args.kwargs
        body = call_kwargs["json"]
        assert body["severity"] == "critical"
        assert body["source"] == "agent"
        assert body["request_url"] == "/api/test"
        assert body["request_status"] == 500
        assert body["traceback"] == "Traceback ..."


class TestListErrorLogs:
    @pytest.mark.asyncio
    async def test_sends_get_with_query_params(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={"logs": [], "count": 0})
        mock_session = _make_request_session(mock_resp)
        client = _make_ops_client(mock_session)

        request = ListErrorLogsRequest(page_size=10, page_no=2, mark_read=True)
        result = await client.list_error_logs(request)

        call_args = mock_session.request.call_args
        assert call_args[0][0] == "GET"
        assert "/logs/error" in str(call_args[0][1])
        call_kwargs = call_args.kwargs
        assert call_kwargs["params"]["page_size"] == "10"
        assert call_kwargs["params"]["page_no"] == "2"
        assert call_kwargs["params"]["mark_read"] == "True"
        assert isinstance(result, ListErrorLogsResponse)

    @pytest.mark.asyncio
    async def test_works_without_request(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={"logs": [], "count": 0})
        mock_session = _make_request_session(mock_resp)
        client = _make_ops_client(mock_session)

        result = await client.list_error_logs()
        assert isinstance(result, ListErrorLogsResponse)
        assert result.count == 0

    @pytest.mark.asyncio
    async def test_deserializes_log_items(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(
            return_value={
                "logs": [
                    {
                        "log_id": "abc-123",
                        "created_at": 1700000000.0,
                        "severity": "error",
                        "source": "manager",
                        "user": "user-1",
                        "is_read": False,
                        "message": "test",
                        "context_lang": "python",
                        "context_env": {"key": "val"},
                        "request_url": None,
                        "request_status": None,
                        "traceback": None,
                    },
                ],
                "count": 1,
            }
        )
        mock_session = _make_request_session(mock_resp)
        client = _make_ops_client(mock_session)

        result = await client.list_error_logs()
        assert result.count == 1
        assert result.logs[0].log_id == "abc-123"
        assert result.logs[0].severity == "error"


class TestClearErrorLog:
    @pytest.mark.asyncio
    async def test_interpolates_log_id_in_path(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={"success": True})
        mock_session = _make_request_session(mock_resp)
        client = _make_ops_client(mock_session)

        result = await client.clear_error_log("log-abc-123")

        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
        assert "/logs/error/log-abc-123/clear" in str(call_args[0][1])
        assert isinstance(result, ClearErrorLogResponse)
        assert result.success is True


class TestGetManagerStatus:
    @pytest.mark.asyncio
    async def test_sends_get_and_deserializes(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(
            return_value={
                "nodes": [
                    {
                        "id": "node-1",
                        "num_proc": 4,
                        "service_addr": "localhost:8080",
                        "heartbeat_timeout": 30.0,
                        "ssl_enabled": False,
                        "active_sessions": 2,
                        "status": "running",
                        "version": "24.12.0",
                        "api_version": 8,
                    },
                ],
                "status": "running",
                "active_sessions": 2,
            }
        )
        mock_session = _make_request_session(mock_resp)
        client = _make_ops_client(mock_session)

        result = await client.get_manager_status()

        call_args = mock_session.request.call_args
        assert call_args[0][0] == "GET"
        assert "/manager/status" in str(call_args[0][1])
        assert isinstance(result, FetchManagerStatusResponse)
        assert result.status == "running"
        assert len(result.nodes) == 1
        assert result.nodes[0].id == "node-1"


class TestUpdateManagerStatus:
    @pytest.mark.asyncio
    async def test_sends_put_with_body(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={})
        mock_session = _make_request_session(mock_resp)
        client = _make_ops_client(mock_session)

        request = UpdateManagerStatusRequest(
            status=ManagerStatus.FROZEN,
            force_kill=True,
        )
        await client.update_manager_status(request)

        call_args = mock_session.request.call_args
        assert call_args[0][0] == "PUT"
        assert "/manager/status" in str(call_args[0][1])
        call_kwargs = call_args.kwargs
        assert call_kwargs["json"]["status"] == "frozen"
        assert call_kwargs["json"]["force_kill"] is True


class TestGetAnnouncement:
    @pytest.mark.asyncio
    async def test_sends_get_and_deserializes(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={"enabled": True, "message": "Maintenance at 10PM"})
        mock_session = _make_request_session(mock_resp)
        client = _make_ops_client(mock_session)

        result = await client.get_announcement()

        call_args = mock_session.request.call_args
        assert call_args[0][0] == "GET"
        assert "/manager/announcement" in str(call_args[0][1])
        assert isinstance(result, GetAnnouncementResponse)
        assert result.enabled is True
        assert result.message == "Maintenance at 10PM"


class TestUpdateAnnouncement:
    @pytest.mark.asyncio
    async def test_sends_post_with_body(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={})
        mock_session = _make_request_session(mock_resp)
        client = _make_ops_client(mock_session)

        request = UpdateAnnouncementRequest(
            enabled=True,
            message="System update scheduled",
        )
        await client.update_announcement(request)

        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
        assert "/manager/announcement" in str(call_args[0][1])
        call_kwargs = call_args.kwargs
        assert call_kwargs["json"]["enabled"] is True
        assert call_kwargs["json"]["message"] == "System update scheduled"


class TestPerformSchedulerOps:
    @pytest.mark.asyncio
    async def test_sends_post_with_body(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={})
        mock_session = _make_request_session(mock_resp)
        client = _make_ops_client(mock_session)

        request = PerformSchedulerOpsRequest(
            op=SchedulerOps.EXCLUDE_AGENTS,
            args=["agent-1", "agent-2"],
        )
        await client.perform_scheduler_ops(request)

        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
        assert "/manager/scheduler/operation" in str(call_args[0][1])
        call_kwargs = call_args.kwargs
        assert call_kwargs["json"]["op"] == "exclude-agents"
        assert call_kwargs["json"]["args"] == ["agent-1", "agent-2"]
