"""Tests for CleanupForceTerminatedHandler."""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from ai.backend.common.events.event_types.kernel.types import KernelLifecycleEventReason
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
from ai.backend.manager.defs import LockID
from ai.backend.manager.sokovan.scheduler.handlers.cleanup import force_terminated
from ai.backend.manager.sokovan.scheduler.handlers.cleanup.force_terminated import (
    MAX_NETWORK_RELEASE_ATTEMPTS,
    CleanupForceTerminatedHandler,
)
from ai.backend.manager.views.sokovan.session import (
    TerminatingKernelData,
    TerminatingSessionData,
)


@pytest.fixture
def mock_terminator() -> AsyncMock:
    terminator = AsyncMock()
    terminator.terminate_sessions_for_handler = AsyncMock(side_effect=_every_agent_accepts)
    return terminator


def _every_agent_accepts(sessions: list[TerminatingSessionData]) -> set[SessionId]:
    return {session.session_id for session in sessions}


@pytest.fixture
def mock_repository() -> AsyncMock:
    repository = AsyncMock()
    repository.get_terminating_sessions_by_ids = AsyncMock(return_value=[])
    repository.search_sessions_with_kernels_for_handler = AsyncMock(return_value=[_A_SESSION])
    return repository


@pytest.fixture
def mock_hook() -> AsyncMock:
    hook = AsyncMock()
    hook.execute = AsyncMock(return_value=None)
    return hook


@pytest.fixture
def mock_hook_registry(mock_hook: AsyncMock) -> MagicMock:
    registry = MagicMock()
    registry.get_hook = MagicMock(return_value=mock_hook)
    return registry


@pytest.fixture
def mock_valkey_schedule() -> AsyncMock:
    valkey = AsyncMock()
    valkey.get_force_terminated_sessions = AsyncMock(return_value=[])
    valkey.remove_force_terminated_sessions = AsyncMock(return_value=None)
    valkey.get_force_terminated_release_attempts = AsyncMock(return_value={})
    valkey.record_force_terminated_release_failure = AsyncMock(return_value=1)
    return valkey


@pytest.fixture
def handler(
    mock_terminator: AsyncMock,
    mock_repository: AsyncMock,
    mock_valkey_schedule: AsyncMock,
    mock_hook_registry: MagicMock,
) -> CleanupForceTerminatedHandler:
    return CleanupForceTerminatedHandler(
        terminator=mock_terminator,
        repository=mock_repository,
        valkey_schedule=mock_valkey_schedule,
        hook_registry=mock_hook_registry,
    )


#: The session+kernel row handed to the TERMINATED hook; only whether the hook ran matters.
_A_SESSION = MagicMock()


def _make_terminating_session_data(session_id: SessionId) -> TerminatingSessionData:
    return TerminatingSessionData(
        session_id=session_id,
        access_key=AccessKey("test-access-key"),
        creation_id="test-creation-id",
        status=SessionStatus.TERMINATED,
        status_info=KernelLifecycleEventReason.FORCE_TERMINATED,
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

    def test_runs_under_its_own_lock(self, handler: CleanupForceTerminatedHandler) -> None:
        assert handler.lock_id == LockID.LOCKID_SOKOVAN_CLEANUP_FORCE_TERMINATED

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
            {sid_ok},
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

    async def test_execute_keeps_a_session_an_agent_refused_to_destroy(
        self,
        handler: CleanupForceTerminatedHandler,
        mock_terminator: AsyncMock,
        mock_repository: AsyncMock,
        mock_valkey_schedule: AsyncMock,
        mock_hook: AsyncMock,
    ) -> None:
        """The terminator reports a refused destroy without raising; the next cycle resends it."""
        sid_refused = SessionId(uuid4())
        sid_ok = SessionId(uuid4())
        mock_repository.get_terminating_sessions_by_ids.return_value = [
            _make_terminating_session_data(sid_refused),
            _make_terminating_session_data(sid_ok),
        ]
        mock_terminator.terminate_sessions_for_handler.side_effect = [set(), {sid_ok}]

        await handler.execute([sid_refused, sid_ok])

        mock_hook.execute.assert_awaited_once_with(_A_SESSION)
        mock_valkey_schedule.record_force_terminated_release_failure.assert_not_awaited()
        mock_valkey_schedule.remove_force_terminated_sessions.assert_awaited_once_with([sid_ok])

    async def test_a_stuck_destroy_times_out_without_holding_up_the_others(
        self,
        handler: CleanupForceTerminatedHandler,
        mock_terminator: AsyncMock,
        mock_repository: AsyncMock,
        mock_valkey_schedule: AsyncMock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """A destroy RPC to an agent that died after it was connected never returns on its own."""
        monkeypatch.setattr(force_terminated, "DESTROY_TIMEOUT_SEC", 0.1)
        sid_stuck = SessionId(uuid4())
        sid_ok = SessionId(uuid4())
        mock_repository.get_terminating_sessions_by_ids.return_value = [
            _make_terminating_session_data(sid_stuck),
            _make_terminating_session_data(sid_ok),
        ]

        async def _destroy(sessions: list[TerminatingSessionData]) -> set[SessionId]:
            if sessions[0].session_id == sid_stuck:
                await asyncio.Event().wait()
            return {sessions[0].session_id}

        mock_terminator.terminate_sessions_for_handler.side_effect = _destroy

        async with asyncio.timeout(5):
            await handler.execute([sid_stuck, sid_ok])

        mock_valkey_schedule.record_force_terminated_release_failure.assert_not_awaited()
        mock_valkey_schedule.remove_force_terminated_sessions.assert_awaited_once_with([sid_ok])

    async def test_a_stuck_destroy_does_not_delay_another_session_s_release(
        self,
        handler: CleanupForceTerminatedHandler,
        mock_terminator: AsyncMock,
        mock_repository: AsyncMock,
        mock_valkey_schedule: AsyncMock,
    ) -> None:
        sid_stuck = SessionId(uuid4())
        sid_ok = SessionId(uuid4())
        mock_repository.get_terminating_sessions_by_ids.return_value = [
            _make_terminating_session_data(sid_stuck),
            _make_terminating_session_data(sid_ok),
        ]
        unstuck = asyncio.Event()
        ok_removed = asyncio.Event()

        async def _destroy(sessions: list[TerminatingSessionData]) -> set[SessionId]:
            if sessions[0].session_id == sid_stuck:
                await unstuck.wait()
            return {sessions[0].session_id}

        async def _remove(ids: list[SessionId]) -> None:
            if ids == [sid_ok]:
                ok_removed.set()

        mock_terminator.terminate_sessions_for_handler.side_effect = _destroy
        mock_valkey_schedule.remove_force_terminated_sessions.side_effect = _remove

        task = asyncio.create_task(handler.execute([sid_stuck, sid_ok]))
        async with asyncio.timeout(5):
            await ok_removed.wait()
        assert not task.done(), "the other session was released only after the stuck one"
        unstuck.set()
        await task

    async def test_what_a_cut_cycle_finished_has_left_the_queue(
        self,
        handler: CleanupForceTerminatedHandler,
        mock_terminator: AsyncMock,
        mock_repository: AsyncMock,
        mock_valkey_schedule: AsyncMock,
    ) -> None:
        """The coordinator cancels a cycle at its lock lifetime; finished sessions stay finished."""
        sid_stuck = SessionId(uuid4())
        sid_ok = SessionId(uuid4())
        mock_repository.get_terminating_sessions_by_ids.return_value = [
            _make_terminating_session_data(sid_stuck),
            _make_terminating_session_data(sid_ok),
        ]

        async def _destroy(sessions: list[TerminatingSessionData]) -> set[SessionId]:
            if sessions[0].session_id == sid_stuck:
                await asyncio.Event().wait()
            return {sessions[0].session_id}

        mock_terminator.terminate_sessions_for_handler.side_effect = _destroy

        with pytest.raises(TimeoutError):
            async with asyncio.timeout(0.2):
                await handler.execute([sid_stuck, sid_ok])

        mock_valkey_schedule.remove_force_terminated_sessions.assert_awaited_once_with([sid_ok])

    async def test_no_more_sessions_than_the_limit_run_at_once(
        self,
        handler: CleanupForceTerminatedHandler,
        mock_terminator: AsyncMock,
        mock_repository: AsyncMock,
        mock_valkey_schedule: AsyncMock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(force_terminated, "MAX_CONCURRENT_SESSIONS", 2)
        session_ids = [SessionId(uuid4()) for _ in range(5)]
        mock_repository.get_terminating_sessions_by_ids.return_value = [
            _make_terminating_session_data(sid) for sid in session_ids
        ]
        running = 0
        peak = 0

        async def _destroy(sessions: list[TerminatingSessionData]) -> set[SessionId]:
            nonlocal running, peak
            running += 1
            peak = max(peak, running)
            await asyncio.sleep(0.01)
            running -= 1
            return {sessions[0].session_id}

        mock_terminator.terminate_sessions_for_handler.side_effect = _destroy

        await handler.execute(session_ids)

        assert peak == 2
        removed = [
            call.args[0][0]
            for call in mock_valkey_schedule.remove_force_terminated_sessions.await_args_list
        ]
        assert sorted(removed) == sorted(session_ids)

    async def test_a_stuck_release_times_out_and_counts_as_a_failed_attempt(
        self,
        handler: CleanupForceTerminatedHandler,
        mock_valkey_schedule: AsyncMock,
        mock_hook: AsyncMock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(force_terminated, "RELEASE_TIMEOUT_SEC", 0.1)
        sid_stuck = SessionId(uuid4())
        sid_ok = SessionId(uuid4())
        mock_valkey_schedule.get_force_terminated_release_attempts.return_value = {
            sid_stuck: 1,
            sid_ok: 1,
        }
        calls = 0

        async def _release(_: Any) -> None:
            nonlocal calls
            calls += 1
            if calls == 1:
                await asyncio.Event().wait()

        mock_hook.execute.side_effect = _release
        mock_valkey_schedule.record_force_terminated_release_failure.return_value = 2

        async with asyncio.timeout(5):
            await handler.execute([sid_stuck, sid_ok])

        mock_valkey_schedule.record_force_terminated_release_failure.assert_awaited_once_with(
            sid_stuck
        )
        mock_valkey_schedule.remove_force_terminated_sessions.assert_awaited_once_with([sid_ok])

    async def test_execute_runs_the_terminated_hook(
        self,
        handler: CleanupForceTerminatedHandler,
        mock_repository: AsyncMock,
        mock_hook: AsyncMock,
        mock_hook_registry: MagicMock,
    ) -> None:
        """A force-terminated session skips the promotion pass, so its TERMINATED hook runs here."""
        session_id = SessionId(uuid4())
        mock_repository.get_terminating_sessions_by_ids.return_value = [
            _make_terminating_session_data(session_id)
        ]

        await handler.execute([session_id])

        mock_hook_registry.get_hook.assert_called_once_with(SessionStatus.TERMINATED)
        mock_hook.execute.assert_awaited_once_with(_A_SESSION)

    async def test_execute_keeps_a_session_whose_network_is_not_back_yet(
        self,
        handler: CleanupForceTerminatedHandler,
        mock_repository: AsyncMock,
        mock_valkey_schedule: AsyncMock,
        mock_hook: AsyncMock,
    ) -> None:
        """A failed network release keeps the id in Valkey so the next cycle retries it."""
        session_id = SessionId(uuid4())
        mock_repository.get_terminating_sessions_by_ids.return_value = [
            _make_terminating_session_data(session_id)
        ]
        mock_hook.execute.side_effect = RuntimeError("overlay allocation is still held")

        await handler.execute([session_id])

        mock_valkey_schedule.record_force_terminated_release_failure.assert_awaited_once_with(
            session_id
        )
        mock_valkey_schedule.remove_force_terminated_sessions.assert_not_awaited()

    async def test_execute_retries_only_the_release_once_destroyed(
        self,
        handler: CleanupForceTerminatedHandler,
        mock_terminator: AsyncMock,
        mock_repository: AsyncMock,
        mock_valkey_schedule: AsyncMock,
        mock_hook: AsyncMock,
    ) -> None:
        """A session whose release failed before is not sent destroy RPCs again."""
        session_id = SessionId(uuid4())
        mock_repository.get_terminating_sessions_by_ids.return_value = [
            _make_terminating_session_data(session_id)
        ]
        mock_valkey_schedule.get_force_terminated_release_attempts.return_value = {session_id: 1}

        await handler.execute([session_id])

        mock_terminator.terminate_sessions_for_handler.assert_not_awaited()
        mock_hook.execute.assert_awaited_once_with(_A_SESSION)
        mock_valkey_schedule.remove_force_terminated_sessions.assert_awaited_once_with([session_id])

    async def test_execute_gives_up_after_the_last_release_attempt(
        self,
        handler: CleanupForceTerminatedHandler,
        mock_terminator: AsyncMock,
        mock_valkey_schedule: AsyncMock,
        mock_hook: AsyncMock,
    ) -> None:
        session_id = SessionId(uuid4())
        mock_valkey_schedule.get_force_terminated_release_attempts.return_value = {
            session_id: MAX_NETWORK_RELEASE_ATTEMPTS - 1
        }
        mock_valkey_schedule.record_force_terminated_release_failure.return_value = (
            MAX_NETWORK_RELEASE_ATTEMPTS
        )
        mock_hook.execute.side_effect = RuntimeError("agent is gone")

        await handler.execute([session_id])

        mock_terminator.terminate_sessions_for_handler.assert_not_awaited()
        mock_valkey_schedule.remove_force_terminated_sessions.assert_awaited_once_with([session_id])

    async def test_execute_keeps_retrying_before_the_last_release_attempt(
        self,
        handler: CleanupForceTerminatedHandler,
        mock_valkey_schedule: AsyncMock,
        mock_hook: AsyncMock,
    ) -> None:
        session_id = SessionId(uuid4())
        mock_valkey_schedule.get_force_terminated_release_attempts.return_value = {session_id: 1}
        mock_valkey_schedule.record_force_terminated_release_failure.return_value = 2
        mock_hook.execute.side_effect = RuntimeError("agent is busy")

        await handler.execute([session_id])

        mock_valkey_schedule.remove_force_terminated_sessions.assert_not_awaited()

    async def test_execute_gives_up_on_a_session_whose_row_is_gone(
        self,
        handler: CleanupForceTerminatedHandler,
        mock_repository: AsyncMock,
        mock_valkey_schedule: AsyncMock,
        mock_hook: AsyncMock,
    ) -> None:
        """Nothing names the network any more, so retrying forever would only keep the id."""
        session_id = SessionId(uuid4())
        mock_repository.get_terminating_sessions_by_ids.return_value = [
            _make_terminating_session_data(session_id)
        ]
        mock_repository.search_sessions_with_kernels_for_handler.return_value = []

        await handler.execute([session_id])

        mock_hook.execute.assert_not_awaited()
        mock_valkey_schedule.remove_force_terminated_sessions.assert_awaited_once_with([session_id])

    async def test_execute_skips_the_hook_when_destroying_raised(
        self,
        handler: CleanupForceTerminatedHandler,
        mock_terminator: AsyncMock,
        mock_repository: AsyncMock,
        mock_valkey_schedule: AsyncMock,
        mock_hook: AsyncMock,
    ) -> None:
        session_id = SessionId(uuid4())
        mock_repository.get_terminating_sessions_by_ids.return_value = [
            _make_terminating_session_data(session_id)
        ]
        # The terminator swallows RPC failures; this stands for an unexpected error inside it.
        mock_terminator.terminate_sessions_for_handler.side_effect = RuntimeError("unexpected")

        await handler.execute([session_id])

        mock_hook.execute.assert_not_awaited()
        mock_valkey_schedule.remove_force_terminated_sessions.assert_not_awaited()

    async def test_execute_removes_the_id_when_no_hook_is_registered(
        self,
        handler: CleanupForceTerminatedHandler,
        mock_repository: AsyncMock,
        mock_valkey_schedule: AsyncMock,
        mock_hook_registry: MagicMock,
    ) -> None:
        session_id = SessionId(uuid4())
        mock_repository.get_terminating_sessions_by_ids.return_value = [
            _make_terminating_session_data(session_id)
        ]
        mock_hook_registry.get_hook.return_value = None

        await handler.execute([session_id])

        mock_repository.search_sessions_with_kernels_for_handler.assert_not_awaited()
        mock_valkey_schedule.remove_force_terminated_sessions.assert_awaited_once_with([session_id])

    async def test_execute_counts_a_failed_session_lookup_and_finishes_the_others(
        self,
        handler: CleanupForceTerminatedHandler,
        mock_repository: AsyncMock,
        mock_valkey_schedule: AsyncMock,
    ) -> None:
        sid_ok = SessionId(uuid4())
        sid_db_error = SessionId(uuid4())
        mock_valkey_schedule.get_force_terminated_release_attempts.return_value = {
            sid_db_error: 1,
            sid_ok: 1,
        }
        mock_repository.search_sessions_with_kernels_for_handler.side_effect = [
            ConnectionError("database is down"),
            [_A_SESSION],
        ]

        await handler.execute([sid_db_error, sid_ok])

        mock_valkey_schedule.record_force_terminated_release_failure.assert_awaited_once_with(
            sid_db_error
        )
        mock_valkey_schedule.remove_force_terminated_sessions.assert_awaited_once_with([sid_ok])

    async def test_execute_keeps_a_session_whose_failure_count_cannot_be_written(
        self,
        handler: CleanupForceTerminatedHandler,
        mock_valkey_schedule: AsyncMock,
        mock_hook: AsyncMock,
    ) -> None:
        sid_ok = SessionId(uuid4())
        sid_valkey_error = SessionId(uuid4())
        mock_valkey_schedule.get_force_terminated_release_attempts.return_value = {
            sid_valkey_error: 1,
            sid_ok: 1,
        }
        mock_hook.execute.side_effect = [RuntimeError("agent is busy"), None]
        mock_valkey_schedule.record_force_terminated_release_failure.side_effect = ConnectionError(
            "valkey is down"
        )

        await handler.execute([sid_valkey_error, sid_ok])

        mock_valkey_schedule.remove_force_terminated_sessions.assert_awaited_once_with([sid_ok])

    async def test_execute_finishes_retried_releases_when_the_destroy_lookup_fails(
        self,
        handler: CleanupForceTerminatedHandler,
        mock_terminator: AsyncMock,
        mock_repository: AsyncMock,
        mock_valkey_schedule: AsyncMock,
    ) -> None:
        sid_new = SessionId(uuid4())
        sid_retried = SessionId(uuid4())
        mock_valkey_schedule.get_force_terminated_release_attempts.return_value = {sid_retried: 1}
        mock_repository.get_terminating_sessions_by_ids.side_effect = ConnectionError(
            "database is down"
        )

        await handler.execute([sid_new, sid_retried])

        mock_terminator.terminate_sessions_for_handler.assert_not_awaited()
        mock_valkey_schedule.remove_force_terminated_sessions.assert_awaited_once_with([
            sid_retried
        ])
