from __future__ import annotations

import asyncio
import logging
import uuid
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncIterator,
    Final,
    Iterable,
    Mapping,
    Optional,
    Tuple,
)
from weakref import WeakSet

import aiohttp_cors
import attrs
import sqlalchemy as sa
import trafaret as t
from aiohttp import web
from aiohttp_sse import sse_response

from ai.backend.common import validators as tx
from ai.backend.common.events.dispatcher import (
    EventDispatcher,
)
from ai.backend.common.events.event_types.kernel.broadcast import (
    BaseKernelEvent,
    KernelCancelledBroadcastEvent,
    KernelCreatingBroadcastEvent,
    KernelPreparingBroadcastEvent,
    KernelPullingBroadcastEvent,
    KernelStartedBroadcastEvent,
    KernelTerminatedBroadcastEvent,
    KernelTerminatingBroadcastEvent,
)
from ai.backend.common.events.event_types.session.broadcast import (
    BaseSessionEvent,
    SchedulingBroadcastEvent,
    SessionCancelledBroadcastEvent,
    SessionEnqueuedBroadcastEvent,
    SessionFailureBroadcastEvent,
    SessionSuccessBroadcastEvent,
    SessionTerminatedBroadcastEvent,
    SessionTerminatingBroadcastEvent,
)
from ai.backend.common.events.hub import WILDCARD
from ai.backend.common.events.hub.propagators.cache import WithCachePropagator
from ai.backend.common.events.types import EventCacheDomain, EventDomain
from ai.backend.common.json import dump_json_str
from ai.backend.common.types import AgentId
from ai.backend.logging import BraceStyleAdapter

from ..errors.common import GenericForbidden
from ..errors.kernel import SessionNotFound
from ..errors.resource import ProjectNotFound
from ..events.hub.propagators.session import SessionEventPropagator
from ..exceptions import InvalidArgument
from ..models import UserRole, groups
from ..models.session import SessionRow
from ..types import Sentinel
from .auth import auth_required
from .manager import READ_ALLOWED, server_status_required
from .utils import check_api_params

if TYPE_CHECKING:
    from .context import RootContext
    from .types import CORSOptions, WebMiddleware

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

sentinel: Final = Sentinel.TOKEN

SessionEventInfo = Tuple[str, dict, str, Optional[int]]


@server_status_required(READ_ALLOWED)
@auth_required
@check_api_params(
    t.Dict({
        tx.AliasedKey(["name", "sessionName"], default="*") >> "session_name": t.String,
        t.Key("ownerAccessKey", default=None) >> "owner_access_key": t.Null | t.String,
        t.Key("sessionId", default=None) >> "session_id": t.Null | tx.UUID,
        # NOTE: if set, sessionId overrides sessionName and ownerAccessKey parameters.
        tx.AliasedKey(["group", "groupName"], default="*") >> "group_name": t.String,
        t.Key("scope", default="*"): t.String,
    })
)
async def push_session_events(
    request: web.Request,
    params: Mapping[str, Any],
) -> web.StreamResponse:
    root_ctx: RootContext = request.app["_root.context"]
    session_name = params["session_name"]
    session_id = params["session_id"]
    scope = params["scope"]
    user_role = request["user"]["role"]
    user_uuid = request["user"]["uuid"]
    access_key = params["owner_access_key"]
    if access_key is None:
        access_key = request["keypair"]["access_key"]
    if user_role == UserRole.USER:
        if access_key != request["keypair"]["access_key"]:
            raise GenericForbidden
    group_name = params["group_name"]
    if scope == "*":
        # Coalesce the legacy default value.
        scope = "session,kernel"

    log.info(
        "PUSH_SESSION_EVENTS (ak:{}, s:{} / s:{}, g:{}, scope:{})",
        access_key,
        session_name,
        session_id,
        group_name,
        scope,
    )
    priv_ctx: PrivateContext = request.app["events.context"]
    current_task = asyncio.current_task()
    assert current_task is not None
    priv_ctx.active_tasks.add(current_task)

    # Resolve session name to session ID
    if session_name == "*":
        session_id = WILDCARD
    else:
        async with root_ctx.db.begin_readonly_session(isolation_level="READ COMMITTED") as db_sess:
            rows = await SessionRow.match_sessions(
                db_sess, session_name, access_key, allow_prefix=False
            )
            if not rows:
                raise SessionNotFound
            session_id = rows[0].id

    # Resolve group name to group ID
    if group_name == "*":
        group_id = WILDCARD
    else:
        async with root_ctx.db.begin_readonly(isolation_level="READ COMMITTED") as conn:
            query = sa.select([groups.c.id]).select_from(groups).where(groups.c.name == group_name)
            result = await conn.execute(query)
            row = result.first()
            if row is None:
                raise ProjectNotFound
            group_id = row["id"]

    filters = {
        "user_role": user_role,
        "user_uuid": user_uuid,
        "domain_name": request["user"]["domain_name"],
        "group_id": group_id,
        "session_name": session_name,
        "session_id": session_id,
        "access_key": access_key,
    }
    aliases = []
    for item in scope.split(","):
        match item:
            case "session":
                aliases.append((EventDomain.SESSION, str(session_id)))
            case "kernel":
                aliases.append((EventDomain.KERNEL, str(session_id)))
            case _:
                raise InvalidArgument(f"Invalid scope: {scope}")

    async with sse_response(request) as resp:
        while not resp.prepared:
            await asyncio.sleep(0.1)
        propagator = SessionEventPropagator(resp, root_ctx.db, filters)
        root_ctx.event_hub.register_event_propagator(propagator, aliases)
        try:
            await resp.wait()
        finally:
            root_ctx.event_hub.unregister_event_propagator(propagator.id())
            await propagator.close()
            return resp


@server_status_required(READ_ALLOWED)
@auth_required
@check_api_params(
    t.Dict({
        tx.AliasedKey(["task_id", "taskId"]): tx.UUID,
    })
)
async def push_background_task_events(
    request: web.Request,
    params: Mapping[str, Any],
) -> web.StreamResponse:
    root_ctx: RootContext = request.app["_root.context"]
    priv_ctx: PrivateContext = request.app["events.context"]
    task_id: uuid.UUID = params["task_id"]
    access_key = request["keypair"]["access_key"]
    log.info("PUSH_BACKGROUND_TASK_EVENTS (ak:{}, t:{})", access_key, task_id)
    current_task = asyncio.current_task()
    assert current_task is not None
    priv_ctx.active_tasks.add(current_task)
    async with sse_response(request) as resp:
        propagator = WithCachePropagator(root_ctx.event_fetcher)
        root_ctx.event_hub.register_event_propagator(
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
            root_ctx.event_hub.unregister_event_propagator(propagator.id())
    return resp


async def _propagate_events(
    app: web.Application,
    agent_id: AgentId,
    event: BaseSessionEvent | BaseKernelEvent | SchedulingBroadcastEvent,
) -> None:
    """
    A private connector from EventDispatcher subscription to EventHub.
    """
    root_ctx: RootContext = app["_root.context"]
    log.trace("api.events._propagate_event({!r})", event)
    await root_ctx.event_hub.propagate_event(event)


@attrs.define(slots=True, auto_attribs=True)
class PrivateContext:
    active_tasks: WeakSet[asyncio.Task[web.StreamResponse]] = attrs.field(factory=WeakSet)


async def events_app_ctx(app: web.Application) -> AsyncIterator[None]:
    """
    Initialize events application context.
    Note: Event subscriptions are now handled by the event hub architecture,
    but we keep the legacy handlers for backward compatibility during transition.
    """
    root_ctx: RootContext = app["_root.context"]
    event_dispatcher: EventDispatcher = root_ctx.event_dispatcher

    # Keep legacy event dispatcher subscriptions for backward compatibility
    # These now delegate to the event hub
    event_dispatcher.subscribe(SessionEnqueuedBroadcastEvent, app, _propagate_events)
    # event_dispatcher.subscribe(SessionScheduledBroadcastEvent, app, _propagate_events)  # replaced by SchedulingBroadcastEvent
    event_dispatcher.subscribe(KernelPreparingBroadcastEvent, app, _propagate_events)
    event_dispatcher.subscribe(KernelPullingBroadcastEvent, app, _propagate_events)
    event_dispatcher.subscribe(KernelCreatingBroadcastEvent, app, _propagate_events)
    event_dispatcher.subscribe(KernelStartedBroadcastEvent, app, _propagate_events)
    # event_dispatcher.subscribe(SessionPreparingBroadcastEvent, app, _propagate_events)  # replaced by SchedulingBroadcastEvent
    # event_dispatcher.subscribe(SessionCreatingBroadcastEvent, app, _propagate_events)  # replaced by SchedulingBroadcastEvent
    # event_dispatcher.subscribe(SessionStartedBroadcastEvent, app, _propagate_events)  # replaced by SchedulingBroadcastEvent
    event_dispatcher.subscribe(KernelTerminatingBroadcastEvent, app, _propagate_events)
    event_dispatcher.subscribe(KernelTerminatedBroadcastEvent, app, _propagate_events)
    event_dispatcher.subscribe(KernelCancelledBroadcastEvent, app, _propagate_events)
    event_dispatcher.subscribe(SessionTerminatingBroadcastEvent, app, _propagate_events)
    event_dispatcher.subscribe(SessionTerminatedBroadcastEvent, app, _propagate_events)
    event_dispatcher.subscribe(SessionCancelledBroadcastEvent, app, _propagate_events)
    event_dispatcher.subscribe(SessionSuccessBroadcastEvent, app, _propagate_events)
    event_dispatcher.subscribe(SessionFailureBroadcastEvent, app, _propagate_events)

    # NOTE: SchedulingBroadcastEvent will replace most other session-related events
    #       since the Sokovan scheduler has been introduced.
    #       Currently its propagation to the Event Hub is already handled in the
    #       scheduler.dispatcher module.
    # FYI: In the future, we don't have to subscribe the events manually as the
    #      event dispatching mechanism will be centralized and migrated into the
    #      Event Hub's implementation detail.
    yield


async def events_shutdown(app: web.Application) -> None:
    """
    Shutdown handler for events app.
    Note: No longer needs to handle session event queues as they are managed by event hub.
    """
    root_ctx: RootContext = app["_root.context"]
    priv_ctx: PrivateContext = app["events.context"]
    await root_ctx.event_hub.shutdown()
    cancelled_tasks = []
    for task in priv_ctx.active_tasks:
        if not task.done():
            task.cancel()
            cancelled_tasks.append(task)
    await asyncio.gather(*cancelled_tasks, return_exceptions=True)


def create_app(
    default_cors_options: CORSOptions,
) -> Tuple[web.Application, Iterable[WebMiddleware]]:
    app = web.Application()
    app["prefix"] = "events"
    app["events.context"] = PrivateContext()
    app["api_versions"] = (3, 4)
    app.on_shutdown.append(events_shutdown)
    cors = aiohttp_cors.setup(app, defaults=default_cors_options)
    add_route = app.router.add_route
    app.cleanup_ctx.append(events_app_ctx)
    cors.add(add_route("GET", r"/background-task", push_background_task_events))
    cors.add(add_route("GET", r"/session", push_session_events))
    return app, []
