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
    SessionTerminatedAnycastEvent,
)
from ai.backend.common.types import (
    AgentId,
    SessionId,
    SessionResult,
    SessionTypes,
)
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


def _make_handler(mock_db: MagicMock) -> tuple[SessionEventHandler, MagicMock]:
    """Create a SessionEventHandler with mocked dependencies.

    Returns the handler and the mock registry so callers can inspect create_task calls.
    """
    mock_registry = MagicMock()
    mock_registry.webhook_ptask_group = MagicMock()
    mock_event_dispatcher_plugin_ctx = MagicMock()
    mock_idle_checker_host = MagicMock()
    handler = SessionEventHandler(
        registry=mock_registry,
        db=mock_db,
        event_dispatcher_plugin_ctx=mock_event_dispatcher_plugin_ctx,
        idle_checker_host=mock_idle_checker_host,
    )
    return handler, mock_registry


async def _invoke_and_capture(
    mock_row: MagicMock,
    event: SessionTerminatedAnycastEvent,
) -> dict[str, Any]:
    """Run invoke_session_callback and return the captured webhook payload data."""
    mock_db_session = AsyncMock()
    mock_db = _make_mock_db(mock_db_session)
    handler, mock_registry = _make_handler(mock_db)

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
        handler, mock_registry = _make_handler(mock_db)

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
