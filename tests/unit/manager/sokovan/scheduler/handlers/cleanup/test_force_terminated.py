"""Tests for CleanupForceTerminatedHandler."""

from __future__ import annotations

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from ai.backend.common.types import (
    AccessKey,
    AgentId,
    KernelId,
    ResourceSlot,
    SessionId,
    SessionTypes,
)
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.repositories.scheduler.types.session import (
    TerminatingKernelData,
    TerminatingSessionData,
)
from ai.backend.manager.sokovan.scheduler.handlers.cleanup.force_terminated import (
    CleanupForceTerminatedHandler,
)


@pytest.fixture
def mock_terminator() -> AsyncMock:
    terminator = AsyncMock()
    terminator.terminate_sessions_for_handler = AsyncMock(return_value=None)
    return terminator


@pytest.fixture
def mock_repository() -> AsyncMock:
    repository = AsyncMock()
    repository.get_terminating_sessions_by_ids = AsyncMock(return_value=[])
    return repository


@pytest.fixture
def mock_valkey_schedule() -> AsyncMock:
    valkey = AsyncMock()
    valkey.get_force_terminated_sessions = AsyncMock(return_value=[])
    valkey.remove_force_terminated_sessions = AsyncMock(return_value=None)
    return valkey


@pytest.fixture
def handler(
    mock_terminator: AsyncMock,
    mock_repository: AsyncMock,
    mock_valkey_schedule: AsyncMock,
) -> CleanupForceTerminatedHandler:
    return CleanupForceTerminatedHandler(
        terminator=mock_terminator,
        repository=mock_repository,
        valkey_schedule=mock_valkey_schedule,
    )


def _make_terminating_session_data(session_id: SessionId) -> TerminatingSessionData:
    return TerminatingSessionData(
        session_id=session_id,
        access_key=AccessKey("test-access-key"),
        creation_id="test-creation-id",
        status=SessionStatus.TERMINATED,
        status_info="FORCE_TERMINATED",
        session_type=SessionTypes.INTERACTIVE,
        kernels=[
            TerminatingKernelData(
                kernel_id=KernelId(uuid4()),
                status=KernelStatus.TERMINATED,
                container_id="container-1",
                agent_id=AgentId("agent-1"),
                agent_addr="tcp://agent-1:6001",
                occupied_slots=ResourceSlot({}),
            ),
        ],
    )


class TestCleanupForceTerminatedHandler:
    def test_name(self) -> None:
        assert CleanupForceTerminatedHandler.name() == "cleanup-force-terminated"

    async def test_fetch_session_ids_delegates_to_valkey(
        self,
        handler: CleanupForceTerminatedHandler,
        mock_valkey_schedule: AsyncMock,
    ) -> None:
        session_ids = [SessionId(uuid4())]
        mock_valkey_schedule.get_force_terminated_sessions.return_value = session_ids

        result = await handler.fetch_session_ids()

        assert list(result) == session_ids

    async def test_execute_sends_rpc_and_removes_succeeded(
        self,
        handler: CleanupForceTerminatedHandler,
        mock_terminator: AsyncMock,
        mock_repository: AsyncMock,
        mock_valkey_schedule: AsyncMock,
    ) -> None:
        session_id = SessionId(uuid4())
        session_data = _make_terminating_session_data(session_id)
        mock_repository.get_terminating_sessions_by_ids.return_value = [session_data]

        await handler.execute([session_id])

        mock_terminator.terminate_sessions_for_handler.assert_awaited_once_with([session_data])
        mock_valkey_schedule.remove_force_terminated_sessions.assert_awaited_once_with([session_id])

    async def test_execute_no_db_data_removes_stale_ids(
        self,
        handler: CleanupForceTerminatedHandler,
        mock_terminator: AsyncMock,
        mock_repository: AsyncMock,
        mock_valkey_schedule: AsyncMock,
    ) -> None:
        """Sessions no longer in DB are removed from Valkey to avoid infinite retry."""
        session_id = SessionId(uuid4())
        mock_repository.get_terminating_sessions_by_ids.return_value = []

        await handler.execute([session_id])

        mock_terminator.terminate_sessions_for_handler.assert_not_awaited()
        mock_valkey_schedule.remove_force_terminated_sessions.assert_awaited_once_with([session_id])

    async def test_execute_partial_failure_removes_only_succeeded(
        self,
        handler: CleanupForceTerminatedHandler,
        mock_terminator: AsyncMock,
        mock_repository: AsyncMock,
        mock_valkey_schedule: AsyncMock,
    ) -> None:
        """Only successfully cleaned sessions are removed from Valkey."""
        sid_ok = SessionId(uuid4())
        sid_fail = SessionId(uuid4())
        data_ok = _make_terminating_session_data(sid_ok)
        data_fail = _make_terminating_session_data(sid_fail)
        mock_repository.get_terminating_sessions_by_ids.return_value = [data_ok, data_fail]

        # First call succeeds, second raises
        mock_terminator.terminate_sessions_for_handler.side_effect = [
            None,
            RuntimeError("Agent unreachable"),
        ]

        await handler.execute([sid_ok, sid_fail])

        # Only the succeeded session ID should be removed
        mock_valkey_schedule.remove_force_terminated_sessions.assert_awaited_once_with([sid_ok])

    async def test_execute_all_fail_removes_nothing(
        self,
        handler: CleanupForceTerminatedHandler,
        mock_terminator: AsyncMock,
        mock_repository: AsyncMock,
        mock_valkey_schedule: AsyncMock,
    ) -> None:
        session_id = SessionId(uuid4())
        session_data = _make_terminating_session_data(session_id)
        mock_repository.get_terminating_sessions_by_ids.return_value = [session_data]
        mock_terminator.terminate_sessions_for_handler.side_effect = RuntimeError("Agent down")

        await handler.execute([session_id])

        mock_valkey_schedule.remove_force_terminated_sessions.assert_not_awaited()
