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
    source: str = "integration-test",
    message: str = "integration test error",
    context_lang: str = "python",
    context_env: dict | None = None,
) -> AppendErrorLogRequest:
    return AppendErrorLogRequest(
        severity=severity,
        source=source,
        message=message,
        context_lang=context_lang,
        context_env=context_env or {"test": "integration"},
    )


@pytest.mark.integration
class TestErrorLogLifecycle:
    @pytest.mark.asyncio
    async def test_append_list_clear_lifecycle(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """append -> list (default) -> verify log present -> mark_cleared -> list -> verify cleared."""
        # 1. Append
        append_result = await admin_registry.error_log.append(
            _make_append_request(message="lifecycle-test-log"),
        )
        assert isinstance(append_result, AppendErrorLogResponse)
        assert append_result.success is True

        # 2. List (default, no query params)
        list_result = await admin_registry.error_log.list_logs()
        assert isinstance(list_result, ListErrorLogsResponse)
        assert list_result.count >= 1
        matching = [entry for entry in list_result.logs if entry.message == "lifecycle-test-log"]
        assert len(matching) >= 1
        log_entry = matching[0]
        assert log_entry.is_cleared is False  # admin sees is_cleared

        # 3. Mark cleared
        log_id = uuid.UUID(log_entry.log_id)
        clear_result = await admin_registry.error_log.mark_cleared(log_id)
        assert isinstance(clear_result, MarkClearedResponse)
        assert clear_result.success is True

        # 4. List again and verify cleared
        list_after = await admin_registry.error_log.list_logs()
        cleared = next(
            (entry for entry in list_after.logs if entry.log_id == str(log_id)),
            None,
        )
        assert cleared is not None
        assert cleared.is_cleared is True

    @pytest.mark.asyncio
    async def test_user_sees_only_own_logs(
        self,
        user_registry: BackendAIClientRegistry,
        second_user_registry: BackendAIClientRegistry,
    ) -> None:
        """user1 appends -> user2 appends -> user1 lists -> only sees own."""
        # user1 appends
        await user_registry.error_log.append(
            _make_append_request(message="user1-log"),
        )
        # user2 appends
        await second_user_registry.error_log.append(
            _make_append_request(message="user2-log"),
        )

        # user1 lists — should see only own logs (non-cleared)
        user1_logs = await user_registry.error_log.list_logs()
        assert isinstance(user1_logs, ListErrorLogsResponse)
        for entry in user1_logs.logs:
            assert entry.message != "user2-log"
            assert entry.is_cleared is None  # non-admin does not see is_cleared

        # user2 lists — should see only own logs
        user2_logs = await second_user_registry.error_log.list_logs()
        assert isinstance(user2_logs, ListErrorLogsResponse)
        for entry in user2_logs.logs:
            assert entry.message != "user1-log"
            assert entry.is_cleared is None

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "Client SDK v2 HMAC signing omits query params; server verifies against"
            " request.raw_path (including ?param=...). Endpoints passing query params"
            " cause 401."
        ),
    )
    @pytest.mark.asyncio
    async def test_list_with_pagination_params(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """append multiple -> list with page_size/page_no."""
        for i in range(3):
            await admin_registry.error_log.append(
                _make_append_request(message=f"paginated-log-{i}"),
            )
        result = await admin_registry.error_log.list_logs(
            ListErrorLogsRequest(page_size=2, page_no=1),
        )
        assert isinstance(result, ListErrorLogsResponse)
        assert len(result.logs) <= 2
