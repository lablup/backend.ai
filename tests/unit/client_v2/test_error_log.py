from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from yarl import URL

from ai.backend.client.v2.base_client import BackendAIClient
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.domains.error_log import ErrorLogClient
from ai.backend.common.dto.manager.error_log import (
    AppendErrorLogRequest,
    AppendErrorLogResponse,
    ListErrorLogsRequest,
    ListErrorLogsResponse,
    MarkClearedResponse,
)

from .conftest import MockAuth

_DEFAULT_CONFIG = ClientConfig(endpoint=URL("https://api.example.com"))

_SAMPLE_ERROR_LOG: dict[str, Any] = {
    "log_id": "550e8400-e29b-41d4-a716-446655440000",
    "created_at": 1700000000.0,
    "severity": "error",
    "source": "webui",
    "user": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
    "is_read": False,
    "message": "Something went wrong",
    "context_lang": "en",
    "context_env": {"browser": "Chrome", "os": "Linux"},
    "request_url": "/api/compute/sessions",
    "request_status": 500,
    "traceback": "Traceback (most recent call last):\n  ...",
    "is_cleared": False,
}


def _make_request_session(resp: AsyncMock) -> MagicMock:
    """Build a mock session whose ``request()`` returns *resp* as a context manager."""
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=resp)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)

    mock_session = MagicMock()
    mock_session.request = MagicMock(return_value=mock_ctx)
    return mock_session


def _make_client(mock_session: MagicMock) -> BackendAIClient:
    return BackendAIClient(_DEFAULT_CONFIG, MockAuth(), mock_session)


def _make_error_log_client(mock_session: MagicMock) -> ErrorLogClient:
    client = _make_client(mock_session)
    return ErrorLogClient(client)


class TestAppendErrorLog:
    @pytest.mark.asyncio
    async def test_append_error_log(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={"success": True})

        mock_session = _make_request_session(mock_resp)
        elc = _make_error_log_client(mock_session)

        request = AppendErrorLogRequest(
            severity="error",
            source="webui",
            message="Something went wrong",
            context_lang="en",
            context_env={"browser": "Chrome"},
            request_url="/api/compute/sessions",
            request_status=500,
            traceback="Traceback ...",
        )
        result = await elc.append(request)

        assert isinstance(result, AppendErrorLogResponse)
        assert result.success is True

        call_args = mock_session.request.call_args
        assert call_args.args[0] == "POST"
        assert "/logs/error" in str(call_args.args[1])
        assert call_args.kwargs["json"]["severity"] == "error"
        assert call_args.kwargs["json"]["source"] == "webui"
        assert call_args.kwargs["json"]["message"] == "Something went wrong"

    @pytest.mark.asyncio
    async def test_append_error_log_minimal(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={"success": True})

        mock_session = _make_request_session(mock_resp)
        elc = _make_error_log_client(mock_session)

        request = AppendErrorLogRequest(
            severity="warning",
            source="agent",
            message="Minor issue",
            context_lang="ko",
            context_env={},
        )
        result = await elc.append(request)

        assert isinstance(result, AppendErrorLogResponse)
        assert result.success is True

        call_args = mock_session.request.call_args
        body = call_args.kwargs["json"]
        assert body["severity"] == "warning"
        assert "request_url" not in body
        assert "request_status" not in body
        assert "traceback" not in body


class TestListErrorLogs:
    @pytest.mark.asyncio
    async def test_list_logs_default(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(
            return_value={
                "logs": [_SAMPLE_ERROR_LOG],
                "count": 1,
            }
        )

        mock_session = _make_request_session(mock_resp)
        elc = _make_error_log_client(mock_session)

        result = await elc.list_logs()

        assert isinstance(result, ListErrorLogsResponse)
        assert len(result.logs) == 1
        assert result.count == 1
        assert result.logs[0].log_id == _SAMPLE_ERROR_LOG["log_id"]
        assert result.logs[0].severity == "error"
        assert result.logs[0].message == "Something went wrong"

        call_args = mock_session.request.call_args
        assert call_args.args[0] == "GET"
        assert "/logs/error" in str(call_args.args[1])
        assert call_args.kwargs["json"] is None

    @pytest.mark.asyncio
    async def test_list_logs_with_params(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(
            return_value={
                "logs": [_SAMPLE_ERROR_LOG],
                "count": 50,
            }
        )

        mock_session = _make_request_session(mock_resp)
        elc = _make_error_log_client(mock_session)

        request = ListErrorLogsRequest(mark_read=True, page_size=10, page_no=2)
        result = await elc.list_logs(request)

        assert isinstance(result, ListErrorLogsResponse)
        assert result.count == 50

        call_args = mock_session.request.call_args
        assert call_args.args[0] == "GET"
        assert call_args.kwargs["params"]["mark_read"] == "True"
        assert call_args.kwargs["params"]["page_size"] == "10"
        assert call_args.kwargs["params"]["page_no"] == "2"

    @pytest.mark.asyncio
    async def test_list_logs_empty(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={"logs": [], "count": 0})

        mock_session = _make_request_session(mock_resp)
        elc = _make_error_log_client(mock_session)

        result = await elc.list_logs()

        assert isinstance(result, ListErrorLogsResponse)
        assert len(result.logs) == 0
        assert result.count == 0


class TestMarkCleared:
    @pytest.mark.asyncio
    async def test_mark_cleared(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={"success": True})

        mock_session = _make_request_session(mock_resp)
        elc = _make_error_log_client(mock_session)

        log_id = uuid4()
        result = await elc.mark_cleared(log_id)

        assert isinstance(result, MarkClearedResponse)
        assert result.success is True

        call_args = mock_session.request.call_args
        assert call_args.args[0] == "POST"
        assert f"/logs/error/{log_id}/clear" in str(call_args.args[1])
        assert call_args.kwargs["json"] is None
