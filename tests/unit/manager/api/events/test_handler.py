"""Regression tests for the background-task SSE event handler."""

from __future__ import annotations

import asyncio
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress
from dataclasses import dataclass
from typing import cast
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiohttp import web
from aiohttp_sse import EventSourceResponse

from ai.backend.common.api_handlers import QueryParam
from ai.backend.common.dto.manager.events.request import PushBackgroundTaskEventsRequest
from ai.backend.common.events.event_types.bgtask.broadcast import BgtaskDoneEvent
from ai.backend.common.events.hub.propagators.cache import WithCachePropagator
from ai.backend.manager.api.rest.events import handler as events_handler
from ai.backend.manager.api.rest.events.handler import EventsHandler, PrivateContext
from ai.backend.manager.dto.context import RequestCtx, UserContext


@pytest.fixture
def propagator() -> WithCachePropagator:
    """The propagator the handler registers (patched in via WithCachePropagator)."""
    fetcher = MagicMock()
    # No cached event -> receive() yields nothing and blocks on its queue,
    # exactly the condition under which the handler used to hang.
    fetcher.fetch_cached_event = AsyncMock(return_value=None)
    return WithCachePropagator(fetcher)


@asynccontextmanager
async def yield_response(response: EventSourceResponse) -> AsyncIterator[EventSourceResponse]:
    """``sse_response(request)`` returns an async CM that yields the response."""
    yield response


@dataclass
class SSEStreamHarness:
    """Handles to a running ``push_background_task_events`` call.

    - ``task``: the handler coroutine, started and blocked in ``receive()``.
    - ``sse``: the response mock; set ``sse.disconnect_event`` to end ``wait()``
      (as a real client disconnect would), assert on ``sse.send``.
    - ``event_hub``: the mock hub, to assert register/unregister calls.
    """

    task: asyncio.Task[web.StreamResponse]
    sse: MagicMock
    event_hub: MagicMock


@pytest.fixture
async def bgtask_event_stream(
    monkeypatch: pytest.MonkeyPatch, propagator: WithCachePropagator
) -> AsyncIterator[SSEStreamHarness]:
    """Start the handler against a mocked SSE response, blocked in receive()."""
    event_hub = MagicMock()
    handler = EventsHandler(
        private_ctx=PrivateContext(),
        events_processors=MagicMock(),
        event_hub=event_hub,
        event_fetcher=MagicMock(),  # unused: WithCachePropagator is patched to `propagator`
    )
    monkeypatch.setattr(events_handler, "WithCachePropagator", lambda _fetcher: propagator)

    # The handler only uses two things on the response: wait() (which returns
    # when the client disconnects) and send(). Model wait() as blocking until we
    # set disconnect_event, i.e. until the client "disconnects".
    sse = MagicMock(spec=EventSourceResponse)
    sse.disconnect_event = asyncio.Event()
    sse.wait.side_effect = sse.disconnect_event.wait
    monkeypatch.setattr(events_handler, "sse_response", lambda _request: yield_response(sse))

    query = MagicMock(spec=QueryParam)
    query.parsed.task_id = uuid.uuid4()
    ctx = MagicMock(spec=RequestCtx)
    ctx.request = MagicMock(spec=web.Request)
    user_ctx = MagicMock(spec=UserContext)
    user_ctx.access_key = "AKIATEST"

    task = asyncio.create_task(
        handler.push_background_task_events(
            cast(QueryParam[PushBackgroundTaskEventsRequest], query),
            cast(RequestCtx, ctx),
            cast(UserContext, user_ctx),
        )
    )
    # Wait until the handler has registered the propagator and is blocked.
    for _ in range(200):
        if event_hub.register_event_propagator.called:
            break
        await asyncio.sleep(0.01)

    try:
        yield SSEStreamHarness(task=task, sse=sse, event_hub=event_hub)
    finally:
        if not task.done():
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task


class TestPushBackgroundTaskEvents:
    async def test_client_disconnect_unregisters_propagator(
        self, bgtask_event_stream: SSEStreamHarness, propagator: WithCachePropagator
    ) -> None:
        """A client disconnecting before the terminal event must not leak.

        The handler blocked forever in ``receive()`` because nothing detected the
        disconnect, so the ``finally`` cleanup never ran and the request task, the
        registered propagator, and its per-alias metric series were never
        released. It must now exit and unregister the propagator once the SSE
        connection closes.
        """
        task = bgtask_event_stream.task
        sse = bgtask_event_stream.sse
        event_hub = bgtask_event_stream.event_hub
        assert not event_hub.unregister_event_propagator.called

        sse.disconnect_event.set()  # the client closes the SSE connection

        try:
            await asyncio.wait_for(task, timeout=5.0)
        except TimeoutError:
            raise AssertionError(
                "handler did not exit after client disconnect (leak regression)"
            ) from None

        event_hub.unregister_event_propagator.assert_called_once_with(propagator.id())

    async def test_terminal_event_completes_and_unregisters(
        self, bgtask_event_stream: SSEStreamHarness, propagator: WithCachePropagator
    ) -> None:
        """The normal path still works: a terminal event ends the stream cleanly."""
        task = bgtask_event_stream.task
        sse = bgtask_event_stream.sse
        event_hub = bgtask_event_stream.event_hub

        # a terminal (done) event arrives -> the handler streams it and stops
        await propagator.propagate_event(BgtaskDoneEvent(task_id=uuid.uuid4(), message="done"))
        try:
            await asyncio.wait_for(task, timeout=5.0)
        except TimeoutError:
            raise AssertionError("handler did not complete after a terminal event") from None

        sse.send.assert_awaited()  # the event was streamed to the client
        event_hub.unregister_event_propagator.assert_called_once()
        assert propagator._closed is True  # the propagator was closed on exit
