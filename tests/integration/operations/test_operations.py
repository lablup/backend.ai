from __future__ import annotations

import pytest

from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.operations import (
    AppendErrorLogRequest,
    GetAnnouncementResponse,
    ListErrorLogsResponse,
    UpdateAnnouncementRequest,
)
from ai.backend.common.dto.manager.operations.types import ErrorLogSeverity


@pytest.mark.integration
class TestErrorLogLifecycle:
    @pytest.mark.asyncio
    async def test_append_list_clear_list(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """append → list (default) → clear → list (verify cleared)."""
        # 1. Append
        append_result = await admin_registry.operations.append_error_log(
            AppendErrorLogRequest(
                severity=ErrorLogSeverity.ERROR,
                source="integration-test",
                message="Integration test error",
                context_lang="python",
                context_env='{"test": true}',
            )
        )
        assert append_result.success is True

        # 2. List (default, no query params)
        list_result = await admin_registry.operations.list_error_logs()
        assert isinstance(list_result, ListErrorLogsResponse)
        assert list_result.count >= 1
        log_id = list_result.logs[0].log_id

        # 3. Clear
        clear_result = await admin_registry.operations.clear_error_log(log_id)
        assert clear_result.success is True

        # 4. List again — cleared log should still appear for admin (is_cleared=True)
        list_result2 = await admin_registry.operations.list_error_logs()
        cleared_log = next((log for log in list_result2.logs if log.log_id == log_id), None)
        assert cleared_log is not None
        assert cleared_log.is_cleared is True


@pytest.mark.integration
class TestAnnouncementLifecycle:
    @pytest.mark.asyncio
    async def test_get_update_get_disable_get(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """get (empty) → update (enable) → get (verify) → update (disable) → get (verify)."""
        # 1. Get default (should be disabled)
        result = await admin_registry.operations.get_announcement()
        assert isinstance(result, GetAnnouncementResponse)
        assert result.enabled is False
        assert result.message == ""

        # 2. Enable announcement
        await admin_registry.operations.update_announcement(
            UpdateAnnouncementRequest(enabled=True, message="Maintenance at 10 PM")
        )

        # 3. Verify enabled
        result = await admin_registry.operations.get_announcement()
        assert result.enabled is True
        assert result.message == "Maintenance at 10 PM"

        # 4. Disable announcement
        await admin_registry.operations.update_announcement(
            UpdateAnnouncementRequest(enabled=False)
        )

        # 5. Verify disabled
        result = await admin_registry.operations.get_announcement()
        assert result.enabled is False
        assert result.message == ""
