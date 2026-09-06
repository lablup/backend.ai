from __future__ import annotations

from collections.abc import Generator
from http import HTTPStatus
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.exception import AgentWatcherResponseError
from ai.backend.common.types import (
    AgentId,
    SessionId,
)
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.errors.agent import (
    AgentHasConflictingSessions,
    ConflictingSessionRescheduleNotSupported,
)
from ai.backend.manager.registry import AgentRegistry
from ai.backend.manager.repositories.agent.repository import AgentRepository
from ai.backend.manager.repositories.scheduler.repository import SchedulerRepository
from ai.backend.manager.services.agent.actions.get_watcher_status import (
    GetWatcherStatusAction,
)
from ai.backend.manager.services.agent.actions.update_resource_group import (
    UpdateAgentResourceGroupAction,
)
from ai.backend.manager.services.agent.actions.watcher_agent_restart import (
    WatcherAgentRestartAction,
)
from ai.backend.manager.services.agent.actions.watcher_agent_start import (
    WatcherAgentStartAction,
)
from ai.backend.manager.services.agent.actions.watcher_agent_stop import (
    WatcherAgentStopAction,
)
from ai.backend.manager.services.agent.service import AgentService
from ai.backend.manager.services.agent.types import ConflictingSessionCleanupPolicy
from ai.backend.manager.sokovan.scheduling_controller import SchedulingController
from ai.backend.manager.views.sokovan.session import MarkTerminatingResult


@pytest.fixture
def mock_etcd() -> AsyncMock:
    return AsyncMock(spec=AsyncEtcd)


@pytest.fixture
def mock_agent_registry() -> AsyncMock:
    return AsyncMock(spec=AgentRegistry)


@pytest.fixture
def mock_config_provider() -> MagicMock:
    mock = MagicMock(spec=ManagerConfigProvider)
    mock.config.watcher.token = "test-token"
    return mock


@pytest.fixture
def mock_agent_repository() -> AsyncMock:
    return AsyncMock(spec=AgentRepository)


@pytest.fixture
def mock_scheduler_repository() -> AsyncMock:
    return AsyncMock(spec=SchedulerRepository)


@pytest.fixture
def mock_scheduling_controller() -> AsyncMock:
    return AsyncMock(spec=SchedulingController)


@pytest.fixture
def agent_service(
    mock_etcd: AsyncMock,
    mock_agent_registry: AsyncMock,
    mock_config_provider: MagicMock,
    mock_agent_repository: AsyncMock,
    mock_scheduler_repository: AsyncMock,
    mock_scheduling_controller: AsyncMock,
) -> AgentService:
    return AgentService(
        etcd=mock_etcd,
        agent_registry=mock_agent_registry,
        config_provider=mock_config_provider,
        agent_repository=mock_agent_repository,
        scheduler_repository=mock_scheduler_repository,
        scheduling_controller=mock_scheduling_controller,
    )


class TestWatcher:
    @pytest.fixture
    def agent_id(self) -> AgentId:
        return AgentId("test-agent-watcher")

    @pytest.fixture
    def _setup_http_mock(self, mock_etcd: AsyncMock) -> Any:
        def _setup(
            agent_id: AgentId, status: int, data: dict[str, Any] | str
        ) -> tuple[AsyncMock, AsyncMock]:
            # Setup etcd
            mock_etcd.get.side_effect = lambda key: {
                f"nodes/agents/{agent_id}/ip": "192.168.1.100",
                f"nodes/agents/{agent_id}/watcher_port": "6099",
            }.get(key)

            # Setup HTTP response
            mock_response = AsyncMock()
            mock_response.status = status
            mock_response.ok = status // 100 == 2
            if isinstance(data, dict):
                mock_response.json = AsyncMock(return_value=data)
            else:
                mock_response.text = AsyncMock(return_value=data)
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock(return_value=None)

            # Setup HTTP session
            mock_session = AsyncMock()
            mock_session.request = MagicMock(return_value=mock_response)
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)

            return mock_session, mock_response

        return _setup

    @pytest.fixture
    def watcher_service_ok(
        self, agent_service: AgentService, agent_id: AgentId, _setup_http_mock: Any
    ) -> Generator[AgentService, None, None]:
        mock_session, _ = _setup_http_mock(agent_id, HTTPStatus.OK, {"result": "ok"})

        with patch(
            "ai.backend.manager.services.agent.service.aiohttp.ClientSession",
            return_value=mock_session,
        ):
            yield agent_service

    @pytest.fixture
    def watcher_service_ok_get(
        self,
        agent_service: AgentService,
        agent_id: AgentId,
        _setup_http_mock: Any,
    ) -> Generator[AgentService, None, None]:
        mock_session, _ = _setup_http_mock(
            agent_id,
            HTTPStatus.OK,
            {"agent-status": "active", "watcher-status": "active"},
        )

        with patch(
            "ai.backend.manager.services.agent.service.aiohttp.ClientSession",
            return_value=mock_session,
        ):
            yield agent_service

    @pytest.fixture
    def watcher_service_forbidden(
        self,
        agent_service: AgentService,
        agent_id: AgentId,
        _setup_http_mock: Any,
    ) -> Generator[AgentService, None, None]:
        mock_session, _ = _setup_http_mock(agent_id, HTTPStatus.FORBIDDEN, "Invalid token")

        with patch(
            "ai.backend.manager.services.agent.service.aiohttp.ClientSession",
            return_value=mock_session,
        ):
            yield agent_service

    @pytest.fixture
    def watcher_service_error(
        self,
        agent_service: AgentService,
        agent_id: AgentId,
        _setup_http_mock: Any,
    ) -> Generator[AgentService, None, None]:
        mock_session, _ = _setup_http_mock(
            agent_id, HTTPStatus.INTERNAL_SERVER_ERROR, "Systemctl command failed"
        )

        with patch(
            "ai.backend.manager.services.agent.service.aiohttp.ClientSession",
            return_value=mock_session,
        ):
            yield agent_service

    async def test_agent_start_success(
        self, watcher_service_ok: AgentService, agent_id: AgentId
    ) -> None:
        # When
        result = await watcher_service_ok.watcher_agent_start(
            WatcherAgentStartAction(agent_id=agent_id)
        )

        # Then
        assert result.data == {"result": "ok"}

    async def test_agent_stop_success(
        self, watcher_service_ok: AgentService, agent_id: AgentId
    ) -> None:
        # When
        result = await watcher_service_ok.watcher_agent_stop(
            WatcherAgentStopAction(agent_id=agent_id)
        )

        # Then
        assert result.data == {"result": "ok"}

    async def test_agent_restart_success(
        self, watcher_service_ok: AgentService, agent_id: AgentId
    ) -> None:
        # When
        result = await watcher_service_ok.watcher_agent_restart(
            WatcherAgentRestartAction(agent_id=agent_id)
        )

        # Then
        assert result.data == {"result": "ok"}

    async def test_get_status_success(
        self, watcher_service_ok_get: AgentService, agent_id: AgentId
    ) -> None:
        # When
        result = await watcher_service_ok_get.get_watcher_status(
            GetWatcherStatusAction(agent_id=agent_id)
        )

        # Then
        assert result.data["agent-status"] == "active"
        assert result.data["watcher-status"] == "active"

    # ==================== Error Tests ====================

    async def test_agent_start_forbidden(
        self, watcher_service_forbidden: AgentService, agent_id: AgentId
    ) -> None:
        # When/Then
        with pytest.raises(AgentWatcherResponseError) as exc_info:
            await watcher_service_forbidden.watcher_agent_start(
                WatcherAgentStartAction(agent_id=agent_id)
            )

        assert exc_info.value.status_code == HTTPStatus.FORBIDDEN
        assert "Agent watcher error" in str(exc_info.value)

    async def test_agent_stop_internal_error(
        self, watcher_service_error: AgentService, agent_id: AgentId
    ) -> None:
        # When/Then
        with pytest.raises(AgentWatcherResponseError) as exc_info:
            await watcher_service_error.watcher_agent_stop(
                WatcherAgentStopAction(agent_id=agent_id)
            )

        assert exc_info.value.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
        assert "Agent watcher error" in str(exc_info.value)


class TestUpdateResourceGroup:
    @pytest.fixture
    def agent_id(self) -> AgentId:
        return AgentId("agent-cleanup")

    @pytest.fixture
    def target_group_id(self) -> ResourceGroupID:
        return ResourceGroupID(uuid4())

    @staticmethod
    def _mark_result(terminating: list[SessionId]) -> MarkTerminatingResult:
        return MarkTerminatingResult(
            cancelled_sessions=[],
            terminating_sessions=terminating,
            force_terminated_sessions=[],
            skipped_sessions=[],
        )

    @staticmethod
    def _kernels(session_ids: list[SessionId]) -> list[MagicMock]:
        """Mimic KernelInfo objects: one kernel per session, exposing session.session_id."""
        return [
            MagicMock(session=MagicMock(session_id=str(session_id))) for session_id in session_ids
        ]

    @staticmethod
    def _action(
        agent_id: AgentId,
        target_group_id: ResourceGroupID,
        *,
        policy: ConflictingSessionCleanupPolicy = ConflictingSessionCleanupPolicy.TERMINATE,
        force: bool = False,
    ) -> UpdateAgentResourceGroupAction:
        return UpdateAgentResourceGroupAction(
            agent_id=agent_id,
            resource_group_id=target_group_id,
            policy=policy,
            force=force,
        )

    async def test_no_conflicts_commits_group_change(
        self,
        agent_service: AgentService,
        mock_agent_repository: AsyncMock,
        mock_scheduling_controller: AsyncMock,
        agent_id: AgentId,
        target_group_id: ResourceGroupID,
    ) -> None:
        # Given the repository reports no active sessions and commits the change
        mock_agent_repository.update_resource_group.return_value = []

        # When
        result = await agent_service.update_resource_group(
            self._action(agent_id, target_group_id, force=False)
        )

        # Then the group is committed without terminating anything
        assert result.resource_group_id == target_group_id
        assert result.conflicting_session_ids == []
        assert result.terminating_session_ids == []
        mock_scheduling_controller.mark_sessions_for_termination.assert_not_called()
        mock_agent_repository.update_resource_group.assert_awaited_once_with(
            agent_id, target_group_id, force=False
        )

    async def test_conflicts_without_force_raises(
        self,
        agent_service: AgentService,
        mock_agent_repository: AsyncMock,
        mock_scheduling_controller: AsyncMock,
        agent_id: AgentId,
        target_group_id: ResourceGroupID,
    ) -> None:
        # Given the repository rejects the change because active sessions remain
        mock_agent_repository.update_resource_group.side_effect = AgentHasConflictingSessions(
            agent_id, 1
        )

        # When / Then the error propagates and nothing is terminated
        with pytest.raises(AgentHasConflictingSessions):
            await agent_service.update_resource_group(
                self._action(agent_id, target_group_id, force=False)
            )

        mock_scheduling_controller.mark_sessions_for_termination.assert_not_called()

    async def test_force_marks_returned_sessions_terminating(
        self,
        agent_service: AgentService,
        mock_agent_repository: AsyncMock,
        mock_scheduling_controller: AsyncMock,
        agent_id: AgentId,
        target_group_id: ResourceGroupID,
    ) -> None:
        # Given the repository commits the change and returns the remaining kernels
        remaining = [SessionId(uuid4()), SessionId(uuid4())]
        mock_agent_repository.update_resource_group.return_value = self._kernels(remaining)
        mock_scheduling_controller.mark_sessions_for_termination.return_value = self._mark_result(
            remaining
        )

        # When
        result = await agent_service.update_resource_group(
            self._action(agent_id, target_group_id, force=True)
        )

        # Then the returned kernels' sessions transition to TERMINATING (graceful)
        mock_agent_repository.update_resource_group.assert_awaited_once_with(
            agent_id, target_group_id, force=True
        )
        call = mock_scheduling_controller.mark_sessions_for_termination.call_args
        assert set(call.args[0]) == set(remaining)
        assert call.kwargs["forced"] is False
        assert set(result.conflicting_session_ids) == set(remaining)
        assert result.terminating_session_ids == remaining
        assert result.resource_group_id == target_group_id

    async def test_reschedule_is_rejected_before_any_change(
        self,
        agent_service: AgentService,
        mock_agent_repository: AsyncMock,
        mock_scheduling_controller: AsyncMock,
        agent_id: AgentId,
        target_group_id: ResourceGroupID,
    ) -> None:
        # When / Then RESCHEDULE is design-only; nothing is changed or terminated
        with pytest.raises(ConflictingSessionRescheduleNotSupported):
            await agent_service.update_resource_group(
                self._action(
                    agent_id,
                    target_group_id,
                    policy=ConflictingSessionCleanupPolicy.RESCHEDULE,
                    force=True,
                )
            )

        mock_agent_repository.update_resource_group.assert_not_called()
        mock_scheduling_controller.mark_sessions_for_termination.assert_not_called()
