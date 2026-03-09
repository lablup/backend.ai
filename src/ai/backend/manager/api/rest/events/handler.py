"""Events handler class using constructor dependency injection.

SSE-based event streaming APIs migrated from module-level functions
to Handler class pattern with typed parameters.
"""

from __future__ import annotations

import asyncio
import logging
from typing import (
    TYPE_CHECKING,
    Any,
    Final,
)
from weakref import WeakSet

import attrs
from aiohttp import web
from aiohttp_sse import sse_response

from ai.backend.common.api_handlers import QueryParam
from ai.backend.common.dto.manager.events.request import (
    PushBackgroundTaskEventsRequest,
    PushSessionEventsRequest,
)
from ai.backend.common.events.hub import WILDCARD
from ai.backend.common.events.hub.propagators.cache import WithCachePropagator
from ai.backend.common.events.types import EventCacheDomain, EventDomain
from ai.backend.common.json import dump_json_str
from ai.backend.common.types import AccessKey
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.dto.context import RequestCtx, UserContext
from ai.backend.manager.errors.common import GenericForbidden
from ai.backend.manager.errors.resource import NoCurrentTaskContext
from ai.backend.manager.exceptions import InvalidArgument
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.services.events.actions.resolve_group_for_events import (
    ResolveGroupForEventsAction,
)
from ai.backend.manager.services.events.actions.resolve_session_for_events import (
    ResolveSessionForEventsAction,
)

if TYPE_CHECKING:
    from ai.backend.common.events.fetcher import EventFetcher
    from ai.backend.common.events.hub.hub import EventHub
    from ai.backend.manager.services.events.processors import EventsProcessors

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


@attrs.define(slots=True, auto_attribs=True)
class PrivateContext:
    active_tasks: WeakSet[asyncio.Task[web.StreamResponse]] = attrs.field(factory=WeakSet)


class EventsHandler:
    """Events API handler with constructor-injected dependencies."""

    def __init__(
        self,
        *,
        private_ctx: PrivateContext,
        events_processors: EventsProcessors,
        event_hub: EventHub,
        event_fetcher: EventFetcher,
    ) -> None:
        self._ctx = private_ctx
        self._events = events_processors
        self.event_hub = event_hub
        self.event_fetcher = event_fetcher

    # ------------------------------------------------------------------
    # push_session_events (GET /events/session)
    # ------------------------------------------------------------------

    async def push_session_events(
        self,
        query: QueryParam[PushSessionEventsRequest],
        ctx: RequestCtx,
        user_ctx: UserContext,
    ) -> web.StreamResponse:
        request = ctx.request
        params = query.parsed
        session_name = params.session_name
        session_id = params.session_id
        scope = params.scope
        user_role = request["user"]["role"]
        user_uuid = user_ctx.user_uuid
        access_key = params.owner_access_key
        if access_key is None:
            access_key = user_ctx.access_key
        if user_role == UserRole.USER:
            if access_key != user_ctx.access_key:
                raise GenericForbidden
        group_name = params.group_name
        if scope == "*":
            scope = "session,kernel"

        log.info(
            "PUSH_SESSION_EVENTS (ak:{}, s:{} / s:{}, g:{}, scope:{})",
            access_key,
            session_name,
            session_id,
            group_name,
            scope,
        )
        priv_ctx = self._ctx
        current_task = asyncio.current_task()
        if current_task is None:
            raise NoCurrentTaskContext("Cannot get current asyncio task for event streaming")
        priv_ctx.active_tasks.add(current_task)

        # Resolve session name to session ID
        if session_name == "*":
            resolved_session_id: Any = WILDCARD
        else:
            resolve_result = await self._events.resolve_session.wait_for_complete(
                ResolveSessionForEventsAction(
                    session_name=session_name, access_key=AccessKey(access_key)
                ),
            )
            resolved_session_id = resolve_result.session_id

        # Resolve group name to group ID
        if group_name == "*":
            group_id: Any = WILDCARD
        else:
            group_result = await self._events.resolve_group.wait_for_complete(
                ResolveGroupForEventsAction(group_name=group_name),
            )
            group_id = group_result.group_id

        filters = {
            "user_role": user_role,
            "user_uuid": user_uuid,
            "domain_name": request["user"]["domain_name"],
            "group_id": group_id,
            "session_name": session_name,
            "session_id": resolved_session_id,
            "access_key": access_key,
        }
        aliases: list[tuple[EventDomain, str]] = []
        for item in scope.split(","):
            match item:
                case "session":
                    aliases.append((EventDomain.SESSION, str(resolved_session_id)))
                case "kernel":
                    aliases.append((EventDomain.KERNEL, str(resolved_session_id)))
                case _:
                    raise InvalidArgument(f"Invalid scope: {scope}")

        async with sse_response(request) as resp:
            ready_event = asyncio.Event()

            async def check_prepared() -> None:
                max_iterations = 50
                for _ in range(max_iterations):
                    if resp.prepared:
                        ready_event.set()
                        return
                    await asyncio.sleep(0.1)
                ready_event.set()

            check_task = asyncio.create_task(check_prepared())
            try:
                await ready_event.wait()
            finally:
                if not check_task.done():
                    check_task.cancel()
                    try:
                        await check_task
                    except asyncio.CancelledError:
                        pass

            propagator = self._events.create_session_propagator(resp, filters)
            self.event_hub.register_event_propagator(propagator, aliases)
            try:
                await resp.wait()
            finally:
                self.event_hub.unregister_event_propagator(propagator.id())
                await propagator.close()
                return resp

    # ------------------------------------------------------------------
    # push_background_task_events (GET /events/background-task)
    # ------------------------------------------------------------------

    async def push_background_task_events(
        self,
        query: QueryParam[PushBackgroundTaskEventsRequest],
        ctx: RequestCtx,
        user_ctx: UserContext,
    ) -> web.StreamResponse:
        request = ctx.request
        priv_ctx = self._ctx
        task_id = query.parsed.task_id
        access_key = user_ctx.access_key
        log.info("PUSH_BACKGROUND_TASK_EVENTS (ak:{}, t:{})", access_key, task_id)
        current_task = asyncio.current_task()
        if current_task is None:
            raise NoCurrentTaskContext(
                "Cannot get current asyncio task for background task streaming"
            )
        priv_ctx.active_tasks.add(current_task)
        async with sse_response(request) as resp:
            propagator = WithCachePropagator(self.event_fetcher)
            self.event_hub.register_event_propagator(
                propagator, [(EventDomain.BGTASK, str(task_id))]
            )
            try:
                cache_id = EventCacheDomain.BGTASK.cache_id(str(task_id))
                async for event in propagator.receive(cache_id):
                    user_event = event.user_event()
                    if user_event is None:
                        log.warning(
                            "Received unsupported user event: {}",
                            event.event_name(),
                        )
                        continue
                    await resp.send(
                        dump_json_str(user_event.user_event_mapping()),
                        event=user_event.event_name(),
                        retry=user_event.retry_count(),
                    )
                    if user_event.is_close_event():
                        log.debug(
                            "Received close event: {}",
                            user_event.event_name(),
                        )
                        break
                await resp.send(dump_json_str({}), event="server_close")
            finally:
                self.event_hub.unregister_event_propagator(propagator.id())
        return resp


# ------------------------------------------------------------------
# Application lifecycle helpers (used by create_app shim)
# ------------------------------------------------------------------


async def events_shutdown(
    _app: web.Application,
    priv_ctx: PrivateContext,
    *,
    event_hub: EventHub,
) -> None:
    """Shutdown handler for events app."""
    await event_hub.shutdown()
    cancelled_tasks: list[asyncio.Task[Any]] = []
    for task in priv_ctx.active_tasks:
        if not task.done():
            task.cancel()
            cancelled_tasks.append(task)
    await asyncio.gather(*cancelled_tasks, return_exceptions=True)
