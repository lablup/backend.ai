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
    valkey.pop_force_terminated_sessions = AsyncMock(return_value=[])
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

    async def test_fetch_session_ids_returns_valkey_data(
        self,
        handler: CleanupForceTerminatedHandler,
        mock_valkey_schedule: AsyncMock,
    ) -> None:
        """fetch_session_ids delegates to Valkey pop."""
        session_ids = [SessionId(uuid4())]
        mock_valkey_schedule.pop_force_terminated_sessions.return_value = session_ids

        result = await handler.fetch_session_ids()

        assert list(result) == session_ids

    async def test_fetch_session_ids_empty(
        self,
        handler: CleanupForceTerminatedHandler,
        mock_valkey_schedule: AsyncMock,
    ) -> None:
        """fetch_session_ids returns empty when Valkey has no entries."""
        mock_valkey_schedule.pop_force_terminated_sessions.return_value = []

        result = await handler.fetch_session_ids()

        assert list(result) == []

    async def test_execute_triggers_cleanup_rpc(
        self,
        handler: CleanupForceTerminatedHandler,
        mock_terminator: AsyncMock,
        mock_repository: AsyncMock,
    ) -> None:
        """execute fetches data from DB and sends RPCs."""
        session_id = SessionId(uuid4())
        session_data = _make_terminating_session_data(session_id)
        mock_repository.get_terminating_sessions_by_ids.return_value = [session_data]

        await handler.execute([session_id])

        mock_repository.get_terminating_sessions_by_ids.assert_awaited_once_with([session_id])
        mock_terminator.terminate_sessions_for_handler.assert_awaited_once_with([session_data])

    async def test_execute_no_db_data_skips_rpc(
        self,
        handler: CleanupForceTerminatedHandler,
        mock_terminator: AsyncMock,
        mock_repository: AsyncMock,
    ) -> None:
        """When DB returns no data, handler skips RPC."""
        session_id = SessionId(uuid4())
        mock_repository.get_terminating_sessions_by_ids.return_value = []

        await handler.execute([session_id])

        mock_terminator.terminate_sessions_for_handler.assert_not_awaited()

    async def test_execute_terminator_exception_is_caught(
        self,
        handler: CleanupForceTerminatedHandler,
        mock_terminator: AsyncMock,
        mock_repository: AsyncMock,
    ) -> None:
        """When terminator raises, handler catches the exception (best-effort cleanup)."""
        session_id = SessionId(uuid4())
        session_data = _make_terminating_session_data(session_id)
        mock_repository.get_terminating_sessions_by_ids.return_value = [session_data]
        mock_terminator.terminate_sessions_for_handler.side_effect = RuntimeError(
            "Agent unreachable"
        )

        # Should not raise — best-effort cleanup
        await handler.execute([session_id])

        mock_terminator.terminate_sessions_for_handler.assert_awaited_once()

    async def test_execute_multiple_sessions(
        self,
        handler: CleanupForceTerminatedHandler,
        mock_terminator: AsyncMock,
        mock_repository: AsyncMock,
    ) -> None:
        """Handler processes multiple force-terminated sessions in a single batch."""
        session_ids = [SessionId(uuid4()) for _ in range(3)]
        session_data = [_make_terminating_session_data(sid) for sid in session_ids]
        mock_repository.get_terminating_sessions_by_ids.return_value = session_data

        await handler.execute(session_ids)

        mock_repository.get_terminating_sessions_by_ids.assert_awaited_once_with(session_ids)
        mock_terminator.terminate_sessions_for_handler.assert_awaited_once_with(session_data)
