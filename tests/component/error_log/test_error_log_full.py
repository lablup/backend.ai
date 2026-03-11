from __future__ import annotations

import uuid
from typing import Any

import pytest

from ai.backend.client.exceptions import BackendAPIError
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
    context_env: dict[str, Any] | None = None,
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


class TestAppendErrorLogFull:
    async def test_admin_appends_with_all_fields(
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

    async def test_admin_appends_with_minimal_fields(
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

    async def test_append_with_different_severity_values(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        for severity in ("debug", "info", "warning", "error", "critical"):
            result = await admin_registry.error_log.append(
                _make_append_request(
                    severity=severity,
                    message=f"log with severity {severity}",
                ),
            )
            assert isinstance(result, AppendErrorLogResponse)
            assert result.success is True


class TestListErrorLogsFull:
    async def test_admin_lists_all_error_logs(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
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
        assert log_entry.is_cleared is not None

    async def test_user_lists_only_own_logs(
        self,
        admin_registry: BackendAIClientRegistry,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        await admin_registry.error_log.append(
            _make_append_request(message="admin log"),
        )
        await user_registry.error_log.append(
            _make_append_request(message="user log"),
        )
        result = await user_registry.error_log.list_logs()
        assert isinstance(result, ListErrorLogsResponse)
        assert result.count >= 1
        for log_entry in result.logs:
            assert log_entry.is_cleared is None

    async def test_admin_sees_all_users_logs(
        self,
        admin_registry: BackendAIClientRegistry,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        await admin_registry.error_log.append(
            _make_append_request(message="admin log for visibility"),
        )
        await user_registry.error_log.append(
            _make_append_request(message="user log for visibility"),
        )
        admin_result = await admin_registry.error_log.list_logs()
        user_result = await user_registry.error_log.list_logs()
        assert isinstance(admin_result, ListErrorLogsResponse)
        assert isinstance(user_result, ListErrorLogsResponse)
        assert admin_result.count >= user_result.count

    async def test_list_with_pagination(
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

    async def test_list_with_mark_read(
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


class TestMarkClearedFull:
    async def test_admin_marks_log_cleared(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        await admin_registry.error_log.append(
            _make_append_request(message="to-be-cleared log"),
        )
        list_result = await admin_registry.error_log.list_logs()
        assert list_result.count >= 1
        log_id = uuid.UUID(list_result.logs[0].log_id)

        result = await admin_registry.error_log.mark_cleared(log_id)
        assert isinstance(result, MarkClearedResponse)
        assert result.success is True

        list_after = await admin_registry.error_log.list_logs()
        cleared_log = next(
            (entry for entry in list_after.logs if entry.log_id == str(log_id)),
            None,
        )
        assert cleared_log is not None
        assert cleared_log.is_cleared is True

    async def test_user_marks_own_log_cleared(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        await user_registry.error_log.append(
            _make_append_request(message="user-clearable log"),
        )
        list_result = await user_registry.error_log.list_logs()
        assert list_result.count >= 1
        log_id = uuid.UUID(list_result.logs[0].log_id)

        result = await user_registry.error_log.mark_cleared(log_id)
        assert isinstance(result, MarkClearedResponse)
        assert result.success is True

    async def test_mark_cleared_nonexistent_log_id(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        nonexistent_id = uuid.uuid4()
        with pytest.raises(BackendAPIError) as exc_info:
            await admin_registry.error_log.mark_cleared(nonexistent_id)
        assert exc_info.value.status == 500

    async def test_user_cannot_clear_another_users_log(
        self,
        admin_registry: BackendAIClientRegistry,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        await admin_registry.error_log.append(
            _make_append_request(message="admin-only log"),
        )
        admin_list = await admin_registry.error_log.list_logs()
        assert admin_list.count >= 1
        admin_log_id = uuid.UUID(admin_list.logs[0].log_id)

        with pytest.raises(BackendAPIError) as exc_info:
            await user_registry.error_log.mark_cleared(admin_log_id)
        assert exc_info.value.status == 500
