"""Unit tests for SessionEventHandler — webhook payload serialization."""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import yarl

from ai.backend.common.events.event_types.session.anycast import (
    ExecutionCancelledAnycastEvent,
    ExecutionFinishedAnycastEvent,
    ExecutionStartedAnycastEvent,
    ExecutionTimeoutAnycastEvent,
    SessionFailureAnycastEvent,
    SessionStartedAnycastEvent,
    SessionStatusTransitionAnycastEvent,
    SessionSuccessAnycastEvent,
    SessionTerminatedAnycastEvent,
)
from ai.backend.common.types import (
    AgentId,
    SessionId,
    SessionResult,
    SessionTypes,
)
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.event_dispatcher.handlers.session import SessionEventHandler


def _make_mock_db(mock_session: AsyncMock) -> MagicMock:
    """Create a mock db engine whose begin_readonly_session() yields the given session."""
    mock_db = MagicMock()

    @asynccontextmanager
    async def _begin_readonly_session(**kwargs: Any) -> AsyncIterator[AsyncMock]:
        yield mock_session

    @asynccontextmanager
    async def _begin_session(**kwargs: Any) -> AsyncIterator[AsyncMock]:
        yield mock_session

    mock_db.begin_readonly_session = _begin_readonly_session
    mock_db.begin_session = _begin_session
    return mock_db


_SENTINEL = object()

_DEFAULT_CALLBACK_URL = yarl.URL("https://example.com/callback")


def _make_mock_session_row(
    *,
    session_type: SessionTypes = SessionTypes.BATCH,
    callback_url: yarl.URL | None | object = _SENTINEL,
    status_history: dict[str, Any] | None = None,
    result: SessionResult | None = SessionResult.SUCCESS,
    status_data: dict[str, Any] | None = None,
) -> MagicMock:
    """Create a mock SessionRow with the given attributes."""
    row = MagicMock()
    row.session_type = session_type
    row.callback_url = _DEFAULT_CALLBACK_URL if callback_url is _SENTINEL else callback_url
    row.status_history = status_history
    row.result = result
    row.status_data = status_data
    return row


def _make_handler(mock_db: MagicMock) -> tuple[SessionEventHandler, MagicMock, AsyncMock]:
    """Create a SessionEventHandler with mocked dependencies.

    Returns the handler with the mock registry and mock valkey-live client so
    callers can inspect create_task and last-access marker calls.
    """
    mock_registry = MagicMock()
    mock_registry.webhook_ptask_group = MagicMock()
    mock_registry.clean_session = AsyncMock()
    mock_event_dispatcher_plugin_ctx = MagicMock()
    mock_event_dispatcher_plugin_ctx.handle_event = AsyncMock()
    mock_scheduling_controller = MagicMock()
    mock_scheduling_controller.mark_sessions_for_termination = AsyncMock()
    mock_valkey_live = AsyncMock()
    handler = SessionEventHandler(
        registry=mock_registry,
        db=mock_db,
        event_dispatcher_plugin_ctx=mock_event_dispatcher_plugin_ctx,
        scheduling_controller=mock_scheduling_controller,
        valkey_live=mock_valkey_live,
    )
    return handler, mock_registry, mock_valkey_live


async def _invoke_and_capture(
    mock_row: MagicMock,
    event: SessionTerminatedAnycastEvent | SessionStatusTransitionAnycastEvent,
) -> dict[str, Any]:
    """Run invoke_session_callback and return the captured webhook payload data."""
    mock_db_session = AsyncMock()
    mock_db = _make_mock_db(mock_db_session)
    handler, mock_registry, _mock_valkey_live = _make_handler(mock_db)

    captured_data: dict[str, Any] = {}

    def _capture(data: dict[str, Any], url: yarl.URL) -> MagicMock:
        captured_data.update(data)
        return MagicMock()

    with (
        patch(
            "ai.backend.manager.event_dispatcher.handlers.session.SessionRow.get_session",
            new_callable=AsyncMock,
            return_value=mock_row,
        ),
        patch(
            "ai.backend.manager.event_dispatcher.handlers.session._make_session_callback",
            new=_capture,
        ),
    ):
        await handler.invoke_session_callback(None, AgentId("i-test"), event)

    return captured_data


class TestInvokeSessionCallbackPayload:
    """Tests for the webhook payload shape built in invoke_session_callback."""

    @pytest.fixture
    def session_id(self) -> SessionId:
        return SessionId(uuid.uuid4())

    @pytest.fixture
    def event(self, session_id: SessionId) -> SessionTerminatedAnycastEvent:
        return SessionTerminatedAnycastEvent(session_id=session_id, reason="user-requested")

    async def test_normal_payload(self, event: SessionTerminatedAnycastEvent) -> None:
        """Populated status_history, result, and status_data should serialize correctly."""
        history = {"PENDING": "2026-01-01T00:00:00", "RUNNING": "2026-01-01T00:01:00"}
        status_data = {"error": {"name": "SomeError", "message": "something failed"}}
        mock_row = _make_mock_session_row(
            status_history=history,
            result=SessionResult.FAILURE,
            status_data=status_data,
        )

        data = await _invoke_and_capture(mock_row, event)

        assert data["status_history"] == history
        assert data["result"] == "FAILURE"
        assert data["status_data"] == status_data

    async def test_empty_status_data_preserved_as_empty_dict(
        self, event: SessionTerminatedAnycastEvent
    ) -> None:
        """Empty dict {} for status_data should serialize as {}, NOT None."""
        mock_row = _make_mock_session_row(
            status_history={"PENDING": "2026-01-01T00:00:00"},
            result=SessionResult.SUCCESS,
            status_data={},
        )

        data = await _invoke_and_capture(mock_row, event)

        assert data["status_data"] == {}
        assert data["status_data"] is not None

    async def test_none_status_data_serialized_as_none(
        self, event: SessionTerminatedAnycastEvent
    ) -> None:
        """None status_data should serialize as None."""
        mock_row = _make_mock_session_row(
            status_history={"PENDING": "2026-01-01T00:00:00"},
            result=SessionResult.SUCCESS,
            status_data=None,
        )

        data = await _invoke_and_capture(mock_row, event)

        assert data["status_data"] is None

    async def test_empty_status_history_preserved_as_empty_dict(
        self, event: SessionTerminatedAnycastEvent
    ) -> None:
        """Empty dict {} for status_history should serialize as {}."""
        mock_row = _make_mock_session_row(
            status_history={},
            result=SessionResult.SUCCESS,
            status_data=None,
        )

        data = await _invoke_and_capture(mock_row, event)

        assert data["status_history"] == {}

    async def test_none_status_history_serialized_as_empty_dict(
        self, event: SessionTerminatedAnycastEvent
    ) -> None:
        """None status_history should serialize as {}."""
        mock_row = _make_mock_session_row(
            status_history=None,
            result=SessionResult.SUCCESS,
            status_data=None,
        )

        data = await _invoke_and_capture(mock_row, event)

        assert data["status_history"] == {}

    async def test_none_result_serialized_as_none(
        self, event: SessionTerminatedAnycastEvent
    ) -> None:
        """None result should serialize as None, not raise AttributeError."""
        mock_row = _make_mock_session_row(
            status_history={},
            result=None,
            status_data=None,
        )

        data = await _invoke_and_capture(mock_row, event)

        assert data["result"] is None

    async def test_no_callback_when_url_is_none(self, event: SessionTerminatedAnycastEvent) -> None:
        """When callback_url is None, no webhook task should be created."""
        mock_row = _make_mock_session_row(callback_url=None)

        mock_db_session = AsyncMock()
        mock_db = _make_mock_db(mock_db_session)
        handler, mock_registry, _mock_valkey_live = _make_handler(mock_db)

        with (
            patch(
                "ai.backend.manager.event_dispatcher.handlers.session.SessionRow.get_session",
                new_callable=AsyncMock,
                return_value=mock_row,
            ),
            patch(
                "ai.backend.manager.event_dispatcher.handlers.session._make_session_callback",
            ) as mock_callback,
        ):
            await handler.invoke_session_callback(None, AgentId("i-test"), event)

        mock_callback.assert_not_called()


class TestSessionActivityMarkers:
    """Tests for the session last-access marker upkeep on session/execution events."""

    @pytest.fixture
    def session_id(self) -> SessionId:
        return SessionId(uuid.uuid4())

    async def test_session_started_initializes_marker(self, session_id: SessionId) -> None:
        handler, _mock_registry, mock_valkey_live = _make_handler(_make_mock_db(AsyncMock()))
        event = SessionStartedAnycastEvent(session_id=session_id, creation_id="creation-id")

        await handler.handle_session_started(None, AgentId("i-test"), event)

        mock_valkey_live.update_session_last_access.assert_awaited_once_with(session_id)

    async def test_session_terminated_deletes_marker(self, session_id: SessionId) -> None:
        handler, _mock_registry, mock_valkey_live = _make_handler(_make_mock_db(AsyncMock()))
        event = SessionTerminatedAnycastEvent(session_id=session_id, reason="user-requested")

        with patch.object(handler, "invoke_session_callback", new=AsyncMock()):
            await handler.handle_session_terminated(None, AgentId("i-test"), event)

        mock_valkey_live.delete_session_last_access.assert_awaited_once_with(session_id)

    async def test_execution_started_marks_session_active(self, session_id: SessionId) -> None:
        handler, _mock_registry, mock_valkey_live = _make_handler(_make_mock_db(AsyncMock()))
        event = ExecutionStartedAnycastEvent(session_id=session_id)

        await handler.handle_execution_started(None, AgentId("i-test"), event)

        mock_valkey_live.mark_session_active.assert_awaited_once_with(session_id)

    @pytest.mark.parametrize(
        "event_cls",
        [
            ExecutionFinishedAnycastEvent,
            ExecutionTimeoutAnycastEvent,
            ExecutionCancelledAnycastEvent,
        ],
    )
    async def test_execution_ended_refreshes_marker(
        self,
        session_id: SessionId,
        event_cls: type[
            ExecutionFinishedAnycastEvent
            | ExecutionTimeoutAnycastEvent
            | ExecutionCancelledAnycastEvent
        ],
    ) -> None:
        handler, _mock_registry, mock_valkey_live = _make_handler(_make_mock_db(AsyncMock()))
        event = event_cls(session_id=session_id)

        await handler.handle_execution_ended(None, AgentId("i-test"), event)

        mock_valkey_live.update_session_last_access.assert_awaited_once_with(session_id)


class TestSessionStatusTransitionCallback:
    """The transition anycast drives one session_lifecycle callback per event."""

    @pytest.mark.parametrize(
        ("status", "expected_event"),
        [
            pytest.param(SessionStatus.PENDING, "enqueued", id="pending"),
            pytest.param(SessionStatus.PREPARING, "checking_precondition", id="preparing"),
            pytest.param(SessionStatus.RUNNING, "started", id="running"),
            pytest.param(SessionStatus.CANCELLED, "cancelled", id="cancelled"),
            pytest.param(SessionStatus.TERMINATING, "terminating", id="terminating"),
            pytest.param(SessionStatus.TERMINATED, "terminated", id="terminated"),
            pytest.param(SessionStatus.RESERVED, "reserved", id="reserved"),
            pytest.param(SessionStatus.PREEMPTED, "preempted", id="preempted"),
            pytest.param(SessionStatus.RESCHEDULING, "rescheduling", id="rescheduling"),
            pytest.param(SessionStatus.DEPRIORITIZING, "deprioritizing", id="deprioritizing"),
            pytest.param(SessionStatus.SCHEDULED, "scheduled", id="scheduled"),
            pytest.param(SessionStatus.PULLING, "pulling", id="pulling"),
            pytest.param(SessionStatus.PREPARED, "prepared", id="prepared"),
            pytest.param(SessionStatus.CREATING, "creating", id="creating"),
        ],
    )
    async def test_status_maps_to_callback_event(
        self, status: SessionStatus, expected_event: str
    ) -> None:
        session_id = SessionId(uuid.uuid4())
        history = {"PENDING": "2026-01-01T00:00:00"}
        event = SessionStatusTransitionAnycastEvent(
            session_id=session_id, status=str(status), reason="test"
        )

        data = await _invoke_and_capture(_make_mock_session_row(status_history=history), event)

        assert data["type"] == "session_lifecycle"
        assert data["event"] == expected_event
        assert data["session_id"] == str(session_id)
        assert data["status_history"] == history
        assert set(data) == {
            "type",
            "event",
            "session_id",
            "when",
            "status_history",
            "result",
            "status_data",
        }

    async def test_one_callback_per_event(self) -> None:
        handler, mock_registry, _ = _make_handler(_make_mock_db(AsyncMock()))
        event = SessionStatusTransitionAnycastEvent(
            session_id=SessionId(uuid.uuid4()), status="RUNNING"
        )

        with (
            patch(
                "ai.backend.manager.event_dispatcher.handlers.session.SessionRow.get_session",
                new_callable=AsyncMock,
                return_value=_make_mock_session_row(session_type=SessionTypes.INTERACTIVE),
            ),
            patch(
                "ai.backend.manager.event_dispatcher.handlers.session._make_session_callback",
                new=MagicMock(),
            ),
        ):
            await handler.invoke_session_callback(None, AgentId("i-test"), event)

        mock_registry.webhook_ptask_group.create_task.assert_called_once()

    @pytest.mark.parametrize(
        ("status", "allow_stale"),
        [
            pytest.param("TERMINATED", True, id="terminated"),
            pytest.param("CANCELLED", True, id="cancelled"),
            pytest.param("RUNNING", False, id="running"),
        ],
    )
    async def test_ended_session_is_read_stale(self, status: str, allow_stale: bool) -> None:
        handler, _, _ = _make_handler(_make_mock_db(AsyncMock()))
        event = SessionStatusTransitionAnycastEvent(
            session_id=SessionId(uuid.uuid4()), status=status
        )

        with patch(
            "ai.backend.manager.event_dispatcher.handlers.session.SessionRow.get_session",
            new_callable=AsyncMock,
            return_value=_make_mock_session_row(callback_url=None),
        ) as get_session:
            await handler.invoke_session_callback(None, AgentId("i-test"), event)

        assert get_session.await_args_list[0].kwargs["allow_stale"] is allow_stale


class TestBatchResultCallback:
    """The agent's batch success/failure path keeps its own callback names."""

    @pytest.mark.parametrize(
        ("event_cls", "expected_event", "success"),
        [
            pytest.param(SessionSuccessAnycastEvent, "success", True, id="success"),
            pytest.param(SessionFailureAnycastEvent, "failure", False, id="failure"),
        ],
    )
    async def test_batch_result_sends_its_callback(
        self,
        event_cls: type[SessionSuccessAnycastEvent] | type[SessionFailureAnycastEvent],
        expected_event: str,
        success: bool,
    ) -> None:
        handler, _, _ = _make_handler(_make_mock_db(AsyncMock()))
        scheduling_controller = MagicMock()
        scheduling_controller.mark_sessions_for_termination = AsyncMock()
        handler._scheduling_controller = scheduling_controller
        session_id = SessionId(uuid.uuid4())
        captured: dict[str, Any] = {}

        def _capture(data: dict[str, Any], url: yarl.URL) -> MagicMock:
            captured.update(data)
            return MagicMock()

        with (
            patch(
                "ai.backend.manager.event_dispatcher.handlers.session.SessionRow.get_session",
                new_callable=AsyncMock,
                return_value=_make_mock_session_row(),
            ),
            patch(
                "ai.backend.manager.event_dispatcher.handlers.session.SessionRow.set_session_result",
                new_callable=AsyncMock,
            ) as set_result,
            patch(
                "ai.backend.manager.event_dispatcher.handlers.session._make_session_callback",
                new=_capture,
            ),
        ):
            await handler.handle_batch_result(
                None, AgentId("i-test"), event_cls(session_id=session_id)
            )

        assert set_result.await_args_list[0].kwargs["success"] is success
        scheduling_controller.mark_sessions_for_termination.assert_awaited_once()
        assert captured["event"] == expected_event
