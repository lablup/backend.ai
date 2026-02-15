"""Unit tests for ExportClient (SDK v2)."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from yarl import URL

from ai.backend.client.v2.base_client import BackendAIClient
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.domains.export import ExportClient
from ai.backend.common.dto.manager.export import (
    GetExportReportResponse,
    ListExportReportsResponse,
    UserExportCSVRequest,
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


def _make_export_client(mock_session: MagicMock) -> ExportClient:
    client = BackendAIClient(_DEFAULT_CONFIG, MockAuth(), mock_session)
    return ExportClient(client)


def _last_request_call(mock_session: MagicMock) -> tuple[str, str, dict[str, Any] | None]:
    """Return (method, url, json_body) from the last ``session.request()`` call."""
    args, kwargs = mock_session.request.call_args
    return args[0], str(args[1]), kwargs.get("json")


# ---------------------------------------------------------------------------
# Sample data factories
# ---------------------------------------------------------------------------

_SAMPLE_FIELD_INFO = {
    "key": "username",
    "name": "Username",
    "description": "The user's login name",
    "field_type": "string",
}

_SAMPLE_REPORT_INFO = {
    "report_key": "users",
    "name": "User Accounts",
    "description": "Export user account data",
    "fields": [_SAMPLE_FIELD_INFO],
}


# ---------------------------------------------------------------------------
# Report endpoints
# ---------------------------------------------------------------------------


class TestReportEndpoints:
    @pytest.mark.asyncio
    async def test_list_reports(self) -> None:
        resp = _json_response({"reports": [_SAMPLE_REPORT_INFO]})
        mock_session = _make_request_session(resp)
        ec = _make_export_client(mock_session)

        result = await ec.list_reports()

        assert isinstance(result, ListExportReportsResponse)
        assert len(result.reports) == 1
        assert result.reports[0].report_key == "users"
        method, url, body = _last_request_call(mock_session)
        assert method == "GET"
        assert url.endswith("/export/reports")
        assert body is None

    @pytest.mark.asyncio
    async def test_get_report(self) -> None:
        resp = _json_response({"report": _SAMPLE_REPORT_INFO})
        mock_session = _make_request_session(resp)
        ec = _make_export_client(mock_session)

        result = await ec.get_report("users")

        assert isinstance(result, GetExportReportResponse)
        assert result.report.report_key == "users"
        method, url, body = _last_request_call(mock_session)
        assert method == "GET"
        assert "/export/reports/users" in url
        assert body is None


# ---------------------------------------------------------------------------
# CSV download endpoints
# ---------------------------------------------------------------------------


class TestCSVDownloadEndpoints:
    @pytest.mark.asyncio
    async def test_download_users_csv(self) -> None:
        mock_client = BackendAIClient(_DEFAULT_CONFIG, MockAuth(), MagicMock())
        ec = ExportClient(mock_client)
        mock_download = AsyncMock(return_value=b"user,email\nalice,a@b.com")

        with patch.object(mock_client, "download", mock_download):
            result = await ec.download_users_csv()

        assert result == b"user,email\nalice,a@b.com"
        mock_download.assert_awaited_once()
        call_args = mock_download.call_args
        assert "/export/users/csv" in call_args.args[0]
        assert call_args.kwargs["json"] is None

    @pytest.mark.asyncio
    async def test_download_sessions_csv(self) -> None:
        mock_client = BackendAIClient(_DEFAULT_CONFIG, MockAuth(), MagicMock())
        ec = ExportClient(mock_client)
        mock_download = AsyncMock(return_value=b"session_id,status\ns1,running")

        with patch.object(mock_client, "download", mock_download):
            result = await ec.download_sessions_csv()

        assert result == b"session_id,status\ns1,running"
        mock_download.assert_awaited_once()
        call_args = mock_download.call_args
        assert "/export/sessions/csv" in call_args.args[0]
        assert call_args.kwargs["json"] is None

    @pytest.mark.asyncio
    async def test_download_projects_csv(self) -> None:
        mock_client = BackendAIClient(_DEFAULT_CONFIG, MockAuth(), MagicMock())
        ec = ExportClient(mock_client)
        mock_download = AsyncMock(return_value=b"project,domain\nproj1,default")

        with patch.object(mock_client, "download", mock_download):
            result = await ec.download_projects_csv()

        assert result == b"project,domain\nproj1,default"
        mock_download.assert_awaited_once()
        call_args = mock_download.call_args
        assert "/export/projects/csv" in call_args.args[0]
        assert call_args.kwargs["json"] is None

    @pytest.mark.asyncio
    async def test_download_keypairs_csv(self) -> None:
        mock_client = BackendAIClient(_DEFAULT_CONFIG, MockAuth(), MagicMock())
        ec = ExportClient(mock_client)
        mock_download = AsyncMock(return_value=b"access_key,secret_key\nAK,SK")

        with patch.object(mock_client, "download", mock_download):
            result = await ec.download_keypairs_csv()

        assert result == b"access_key,secret_key\nAK,SK"
        mock_download.assert_awaited_once()
        call_args = mock_download.call_args
        assert "/export/keypairs/csv" in call_args.args[0]
        assert call_args.kwargs["json"] is None

    @pytest.mark.asyncio
    async def test_download_audit_logs_csv(self) -> None:
        mock_client = BackendAIClient(_DEFAULT_CONFIG, MockAuth(), MagicMock())
        ec = ExportClient(mock_client)
        mock_download = AsyncMock(return_value=b"timestamp,action\n2025-01-01,login")

        with patch.object(mock_client, "download", mock_download):
            result = await ec.download_audit_logs_csv()

        assert result == b"timestamp,action\n2025-01-01,login"
        mock_download.assert_awaited_once()
        call_args = mock_download.call_args
        assert "/export/audit-logs/csv" in call_args.args[0]
        assert call_args.kwargs["json"] is None


# ---------------------------------------------------------------------------
# Request body handling
# ---------------------------------------------------------------------------


class TestRequestBodyHandling:
    @pytest.mark.asyncio
    async def test_download_users_csv_with_request_body(self) -> None:
        mock_client = BackendAIClient(_DEFAULT_CONFIG, MockAuth(), MagicMock())
        ec = ExportClient(mock_client)
        mock_download = AsyncMock(return_value=b"csv-data")

        request = UserExportCSVRequest(
            fields=["username", "email"],
            encoding="utf-8",
        )

        with patch.object(mock_client, "download", mock_download):
            result = await ec.download_users_csv(request)

        assert result == b"csv-data"
        call_args = mock_download.call_args
        json_body = call_args.kwargs["json"]
        assert json_body is not None
        assert json_body["fields"] == ["username", "email"]
        assert json_body["encoding"] == "utf-8"

    @pytest.mark.asyncio
    async def test_download_users_csv_without_request(self) -> None:
        mock_client = BackendAIClient(_DEFAULT_CONFIG, MockAuth(), MagicMock())
        ec = ExportClient(mock_client)
        mock_download = AsyncMock(return_value=b"csv-data")

        with patch.object(mock_client, "download", mock_download):
            result = await ec.download_users_csv(None)

        assert result == b"csv-data"
        call_args = mock_download.call_args
        assert call_args.kwargs["json"] is None
