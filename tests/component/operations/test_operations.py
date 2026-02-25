from __future__ import annotations

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.client.v2.registry import BackendAIClientRegistry
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
from ai.backend.manager.models.agent import agents


class TestAppendErrorLog:
    @pytest.mark.asyncio
    async def test_admin_appends_error_log(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        result = await admin_registry.operations.append_error_log(
            AppendErrorLogRequest(
                severity=ErrorLogSeverity.ERROR,
                source="test-admin",
                message="Test error from admin",
                context_lang="python",
                context_env='{"test": true}',
            )
        )
        assert isinstance(result, AppendErrorLogResponse)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_user_appends_error_log(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        result = await user_registry.operations.append_error_log(
            AppendErrorLogRequest(
                severity=ErrorLogSeverity.WARNING,
                source="test-user",
                message="Test warning from user",
                context_lang="python",
                context_env="{}",
            )
        )
        assert isinstance(result, AppendErrorLogResponse)
        assert result.success is True


class TestListErrorLogs:
    @pytest.mark.asyncio
    async def test_admin_lists_error_logs_default(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        await admin_registry.operations.append_error_log(
            AppendErrorLogRequest(
                severity=ErrorLogSeverity.ERROR,
                source="test",
                message="Test error for listing",
                context_lang="python",
                context_env="{}",
            )
        )
        result = await admin_registry.operations.list_error_logs()
        assert isinstance(result, ListErrorLogsResponse)
        assert result.count >= 1
        assert len(result.logs) >= 1

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "Client SDK v2 HMAC signing omits query params; server verifies against"
            " request.raw_path (including ?param=...). Endpoints passing query params"
            " cause 401."
        ),
    )
    @pytest.mark.asyncio
    async def test_admin_lists_error_logs_with_params(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        result = await admin_registry.operations.list_error_logs(
            ListErrorLogsRequest(page_size=10, page_no=1, mark_read=False)
        )
        assert isinstance(result, ListErrorLogsResponse)

    @pytest.mark.asyncio
    async def test_user_lists_own_error_logs(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        await user_registry.operations.append_error_log(
            AppendErrorLogRequest(
                severity=ErrorLogSeverity.ERROR,
                source="test-user",
                message="User-visible error",
                context_lang="python",
                context_env="{}",
            )
        )
        result = await user_registry.operations.list_error_logs()
        assert isinstance(result, ListErrorLogsResponse)
        assert result.count >= 1
        assert len(result.logs) >= 1


class TestClearErrorLog:
    @pytest.mark.asyncio
    async def test_admin_clears_error_log(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        await admin_registry.operations.append_error_log(
            AppendErrorLogRequest(
                severity=ErrorLogSeverity.ERROR,
                source="test",
                message="Error to clear",
                context_lang="python",
                context_env="{}",
            )
        )
        logs = await admin_registry.operations.list_error_logs()
        assert logs.count >= 1
        log_id = logs.logs[0].log_id

        result = await admin_registry.operations.clear_error_log(log_id)
        assert isinstance(result, ClearErrorLogResponse)
        assert result.success is True


class TestGetManagerStatus:
    @pytest.mark.asyncio
    async def test_admin_gets_manager_status(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        result = await admin_registry.operations.get_manager_status()
        assert isinstance(result, FetchManagerStatusResponse)
        assert result.status == "running"
        assert len(result.nodes) >= 1


class TestUpdateManagerStatus:
    @pytest.mark.asyncio
    async def test_superadmin_updates_manager_status(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        await admin_registry.operations.update_manager_status(
            UpdateManagerStatusRequest(status=ManagerStatus.FROZEN)
        )
        # Restore to running for subsequent tests
        await admin_registry.operations.update_manager_status(
            UpdateManagerStatusRequest(status=ManagerStatus.RUNNING)
        )


class TestGetAnnouncement:
    @pytest.mark.asyncio
    async def test_admin_gets_announcement(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        result = await admin_registry.operations.get_announcement()
        assert isinstance(result, GetAnnouncementResponse)
        assert result.enabled is False
        assert result.message == ""


class TestUpdateAnnouncement:
    @pytest.mark.asyncio
    async def test_superadmin_updates_announcement(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        await admin_registry.operations.update_announcement(
            UpdateAnnouncementRequest(enabled=True, message="Test announcement")
        )
        result = await admin_registry.operations.get_announcement()
        assert result.enabled is True
        assert result.message == "Test announcement"

        # Cleanup: disable announcement
        await admin_registry.operations.update_announcement(
            UpdateAnnouncementRequest(enabled=False)
        )
        result = await admin_registry.operations.get_announcement()
        assert result.enabled is False


class TestPerformSchedulerOps:
    @pytest.mark.asyncio
    async def test_superadmin_excludes_agents(
        self,
        admin_registry: BackendAIClientRegistry,
        agent_fixture: str,
        db_engine: SAEngine,
    ) -> None:
        await admin_registry.operations.perform_scheduler_ops(
            PerformSchedulerOpsRequest(
                op=SchedulerOps.EXCLUDE_AGENTS,
                args=[agent_fixture],
            )
        )
        async with db_engine.begin() as conn:
            result = await conn.execute(
                sa.select(agents.c.schedulable).where(agents.c.id == agent_fixture)
            )
            assert result.scalar_one() is False

    @pytest.mark.asyncio
    async def test_superadmin_includes_agents(
        self,
        admin_registry: BackendAIClientRegistry,
        agent_fixture: str,
        db_engine: SAEngine,
    ) -> None:
        # First exclude
        await admin_registry.operations.perform_scheduler_ops(
            PerformSchedulerOpsRequest(
                op=SchedulerOps.EXCLUDE_AGENTS,
                args=[agent_fixture],
            )
        )
        # Then include
        await admin_registry.operations.perform_scheduler_ops(
            PerformSchedulerOpsRequest(
                op=SchedulerOps.INCLUDE_AGENTS,
                args=[agent_fixture],
            )
        )
        async with db_engine.begin() as conn:
            result = await conn.execute(
                sa.select(agents.c.schedulable).where(agents.c.id == agent_fixture)
            )
            assert result.scalar_one() is True
