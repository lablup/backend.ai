"""Owner checks on the ``schedulingEventsBySession`` subscription."""

from __future__ import annotations

import uuid
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock

import pytest
import strawberry

from ai.backend.common.events.event_types.session.broadcast import SchedulingBroadcastEvent
from ai.backend.common.events.types import EventDomain
from ai.backend.common.types import SessionId
from ai.backend.manager.api.gql import scheduler as scheduler_gql
from ai.backend.manager.errors.kernel import InvalidSessionId
from ai.backend.manager.errors.permission import NotEnoughPermission

_RESOLVER = cast(Any, scheduler_gql.scheduling_events_by_session).base_resolver


class _Propagator:
    """Stands in for ``AsyncBypassPropagator``, replaying a fixed event list."""

    def __init__(self, events: list[Any]) -> None:
        self._events = events

    def id(self) -> uuid.UUID:
        return uuid.uuid4()

    async def receive(self) -> Any:
        for event in self._events:
            yield event


def _info(session_get: AsyncMock) -> MagicMock:
    info = MagicMock()
    info.context.adapters.session.get = session_get
    return info


def _scheduling_event(session_id: SessionId) -> SchedulingBroadcastEvent:
    return SchedulingBroadcastEvent(
        session_id=session_id,
        creation_id="creation",
        status_transition="SCHEDULED",
        reason="ok",
    )


@pytest.fixture
def session_id() -> SessionId:
    return SessionId(uuid.uuid4())


@pytest.fixture
def readable_session() -> AsyncMock:
    return AsyncMock(return_value=MagicMock())


class TestSchedulingEventsSubscription:
    async def test_refuses_a_session_the_caller_cannot_read(
        self, monkeypatch: pytest.MonkeyPatch, session_id: SessionId
    ) -> None:
        refused = AsyncMock(side_effect=NotEnoughPermission("no read on this session"))
        info = _info(refused)
        monkeypatch.setattr(scheduler_gql, "AsyncBypassPropagator", lambda: _Propagator([]))

        stream = _RESOLVER(session_id=strawberry.ID(str(session_id)), info=info)
        with pytest.raises(NotEnoughPermission):
            await anext(stream)

        info.context.event_hub.register_event_propagator.assert_not_called()

    async def test_streams_events_for_a_readable_session(
        self,
        monkeypatch: pytest.MonkeyPatch,
        session_id: SessionId,
        readable_session: AsyncMock,
    ) -> None:
        info = _info(readable_session)
        propagator = _Propagator([_scheduling_event(session_id)])
        monkeypatch.setattr(scheduler_gql, "AsyncBypassPropagator", lambda: propagator)

        payloads = [
            payload
            async for payload in _RESOLVER(session_id=strawberry.ID(str(session_id)), info=info)
        ]

        assert [payload.status_transition for payload in payloads] == ["SCHEDULED"]
        readable_session.assert_awaited_once_with(session_id)
        _, kwargs = info.context.event_hub.register_event_propagator.call_args
        assert kwargs["aliases"] == [(EventDomain.SESSION, str(session_id))]

    async def test_reads_the_session_before_registering_the_propagator(
        self,
        monkeypatch: pytest.MonkeyPatch,
        session_id: SessionId,
        readable_session: AsyncMock,
    ) -> None:
        order: list[str] = []

        def read(_: SessionId) -> MagicMock:
            order.append("read")
            return MagicMock()

        readable_session.side_effect = read
        info = _info(readable_session)
        info.context.event_hub.register_event_propagator.side_effect = (
            lambda *args, **kwargs: order.append("register")
        )
        monkeypatch.setattr(scheduler_gql, "AsyncBypassPropagator", lambda: _Propagator([]))

        async for _ in _RESOLVER(session_id=strawberry.ID(str(session_id)), info=info):
            pass

        assert order == ["read", "register"]

    async def test_rejects_a_malformed_session_id(self, readable_session: AsyncMock) -> None:
        info = _info(readable_session)

        stream = _RESOLVER(session_id=strawberry.ID("not-a-uuid"), info=info)
        with pytest.raises(InvalidSessionId):
            await anext(stream)

        readable_session.assert_not_awaited()
