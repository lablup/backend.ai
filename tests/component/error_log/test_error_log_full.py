from __future__ import annotations

import uuid
from typing import Any

import pytest

from ai.backend.client.exceptions import BackendAPIError
from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.error_log import (
    AppendErrorLogRequest,
    AppendErrorLogResponse,
    ListErrorLogsResponse,
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


class TestMarkClearedFull:
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
