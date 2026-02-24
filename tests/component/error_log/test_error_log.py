from __future__ import annotations

import uuid

import pytest

from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.error_log import (
    AppendErrorLogRequest,
    AppendErrorLogResponse,
    ListErrorLogsRequest,
    ListErrorLogsResponse,
    MarkClearedResponse,
)


def _make_append_request(
    *,
    severity: str = "error",
    source: str = "test-source",
    message: str = "test error message",
    context_lang: str = "python",
    context_env: dict | None = None,
    request_url: str | None = None,
    request_status: int | None = None,
    traceback: str | None = None,
) -> AppendErrorLogRequest:
    return AppendErrorLogRequest(
        severity=severity,
        source=source,
        message=message,
        context_lang=context_lang,
        context_env=context_env or {"key": "value"},
        request_url=request_url,
        request_status=request_status,
        traceback=traceback,
    )


class TestAppendErrorLog:
    @pytest.mark.asyncio
    async def test_admin_appends_error_log(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        result = await admin_registry.error_log.append(
            _make_append_request(
                severity="error",
                source="admin-test",
                message="full error from admin",
                context_lang="python",
                context_env={"runtime": "cpython", "version": "3.12"},
                request_url="https://example.com/api/test",
                request_status=500,
                traceback="Traceback (most recent call last):\n  ...",
            ),
        )
        assert isinstance(result, AppendErrorLogResponse)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_admin_appends_error_log_minimal(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        result = await admin_registry.error_log.append(
            _make_append_request(
                severity="warning",
                source="minimal-test",
                message="minimal error log",
            ),
        )
        assert isinstance(result, AppendErrorLogResponse)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_user_appends_error_log(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        result = await user_registry.error_log.append(
            _make_append_request(
                severity="critical",
                source="user-test",
                message="error from regular user",
            ),
        )
        assert isinstance(result, AppendErrorLogResponse)
        assert result.success is True


class TestListErrorLogs:
    @pytest.mark.asyncio
    async def test_admin_lists_error_logs(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        # Create a log entry first
        await admin_registry.error_log.append(
            _make_append_request(message="admin-visible log"),
        )
        result = await admin_registry.error_log.list_logs()
        assert isinstance(result, ListErrorLogsResponse)
        assert result.count >= 1
        assert len(result.logs) >= 1
        log_entry = result.logs[0]
        assert log_entry.log_id
        assert log_entry.severity
        assert log_entry.is_cleared is not None  # admin sees is_cleared

    @pytest.mark.asyncio
    async def test_user_lists_own_error_logs(
        self,
        admin_registry: BackendAIClientRegistry,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        # Admin creates a log
        await admin_registry.error_log.append(
            _make_append_request(message="admin log"),
        )
        # User creates a log
        await user_registry.error_log.append(
            _make_append_request(message="user log"),
        )
        result = await user_registry.error_log.list_logs()
        assert isinstance(result, ListErrorLogsResponse)
        # User should only see their own logs
        assert result.count >= 1
        for log_entry in result.logs:
            assert log_entry.is_cleared is None  # non-admin does not see is_cleared

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "Client SDK v2 HMAC signing omits query params; server verifies against"
            " request.raw_path (including ?param=...). Endpoints passing query params"
            " cause 401."
        ),
    )
    @pytest.mark.asyncio
    async def test_list_logs_with_query_params(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        await admin_registry.error_log.append(
            _make_append_request(message="paginated log"),
        )
        result = await admin_registry.error_log.list_logs(
            ListErrorLogsRequest(page_size=10, page_no=1),
        )
        assert isinstance(result, ListErrorLogsResponse)

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "Client SDK v2 HMAC signing omits query params; server verifies against"
            " request.raw_path (including ?param=...). Endpoints passing query params"
            " cause 401."
        ),
    )
    @pytest.mark.asyncio
    async def test_list_logs_with_mark_read(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        await admin_registry.error_log.append(
            _make_append_request(message="to-be-read log"),
        )
        result = await admin_registry.error_log.list_logs(
            ListErrorLogsRequest(mark_read=True),
        )
        assert isinstance(result, ListErrorLogsResponse)


class TestMarkCleared:
    @pytest.mark.asyncio
    async def test_admin_marks_log_cleared(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        # Create a log entry
        await admin_registry.error_log.append(
            _make_append_request(message="to-be-cleared log"),
        )
        # List to get the log_id
        list_result = await admin_registry.error_log.list_logs()
        assert list_result.count >= 1
        log_id = uuid.UUID(list_result.logs[0].log_id)

        result = await admin_registry.error_log.mark_cleared(log_id)
        assert isinstance(result, MarkClearedResponse)
        assert result.success is True

        # Verify it is cleared
        list_after = await admin_registry.error_log.list_logs()
        cleared_log = next(
            (entry for entry in list_after.logs if entry.log_id == str(log_id)),
            None,
        )
        assert cleared_log is not None
        assert cleared_log.is_cleared is True

    @pytest.mark.asyncio
    async def test_user_marks_own_log_cleared(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        # User creates a log entry
        await user_registry.error_log.append(
            _make_append_request(message="user-clearable log"),
        )
        # List to get the log_id (user only sees own, non-cleared logs)
        list_result = await user_registry.error_log.list_logs()
        assert list_result.count >= 1
        log_id = uuid.UUID(list_result.logs[0].log_id)

        result = await user_registry.error_log.mark_cleared(log_id)
        assert isinstance(result, MarkClearedResponse)
        assert result.success is True
