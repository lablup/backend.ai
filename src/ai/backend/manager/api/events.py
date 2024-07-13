from __future__ import annotations

import asyncio
import json
import logging
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncIterator,
    Final,
    Iterable,
    Mapping,
    Optional,
    Set,
    Tuple,
    Union,
)

import aiohttp_cors
import attrs
import sqlalchemy as sa
import trafaret as t
from aiohttp import web
from aiohttp_sse import sse_response
from aiotools import adefer
from sqlalchemy.orm import load_only

from ai.backend.common import validators as tx
from ai.backend.common.events import (
    BgtaskCancelledEvent,
    BgtaskDoneEvent,
    BgtaskFailedEvent,
    BgtaskUpdatedEvent,
    EventDispatcher,
    KernelCancelledEvent,
    KernelCreatingEvent,
    KernelPreparingEvent,
    KernelPullingEvent,
    KernelStartedEvent,
    KernelTerminatedEvent,
    KernelTerminatingEvent,
    SessionCancelledEvent,
    SessionEnqueuedEvent,
    SessionFailureEvent,
    SessionScheduledEvent,
    SessionStartedEvent,
    SessionSuccessEvent,
    SessionTerminatedEvent,
    SessionTerminatingEvent,
)
from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common.types import AgentId

from ..models import UserRole, groups, kernels
from ..models.session import SessionRow
from ..models.utils import execute_with_retry
from ..types import Sentinel
from .auth import auth_required
from .exceptions import GenericForbidden, GroupNotFound, ObjectNotFound
from .manager import READ_ALLOWED, server_status_required
from .utils import check_api_params

if TYPE_CHECKING:
    from .context import RootContext
    from .types import CORSOptions, WebMiddleware

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]

sentinel: Final = Sentinel.token

SessionEventInfo = Tuple[str, dict, str, Optional[int]]
BgtaskEvents = Union[BgtaskUpdatedEvent, BgtaskDoneEvent, BgtaskCancelledEvent, BgtaskFailedEvent]


@server_status_required(READ_ALLOWED)
@auth_required
@check_api_params(
    t.Dict({
        tx.AliasedKey(["name", "sessionName"], default="*") >> "session_name": t.String,
        t.Key("ownerAccessKey", default=None) >> "owner_access_key": t.Null | t.String,
        t.Key("sessionId", default=None) >> "session_id": t.Null | tx.UUID,
        # NOTE: if set, sessionId overrides sessionName and ownerAccessKey parameters.
        tx.AliasedKey(["group", "groupName"], default="*") >> "group_name": t.String,
        t.Key("scope", default="*"): t.Enum("*", "session", "kernel"),
    })
)
@adefer
async def push_session_events(
    defer,
    request: web.Request,
    params: Mapping[str, Any],
) -> web.StreamResponse:
    root_ctx: RootContext = request.app["_root.context"]
    app_ctx: PrivateContext = request.app["events.context"]
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
    my_queue: asyncio.Queue[Sentinel | SessionEventInfo] = asyncio.Queue()
    log.info("PUSH_SESSION_EVENTS (ak:{}, s:{}, g:{})", access_key, session_name, group_name)
    if group_name == "*":
        group_id = "*"
    else:
        async with root_ctx.db.begin_readonly() as conn:
            query = sa.select([groups.c.id]).select_from(groups).where(groups.c.name == group_name)
            result = await conn.execute(query)
            row = result.first()
            if row is None:
                raise GroupNotFound
            group_id = row["id"]
    app_ctx.session_event_queues.add(my_queue)
    defer(lambda: app_ctx.session_event_queues.remove(my_queue))
    async with sse_response(request) as resp:
        try:
            while True:
                evdata = await my_queue.get()
                try:
                    if evdata is sentinel:
                        break
                    event_name, row, reason, exit_code = evdata
                    if user_role in (UserRole.USER, UserRole.ADMIN):
                        if row["domain_name"] != request["user"]["domain_name"]:
                            continue
                    if user_role == UserRole.USER:
                        if row["user_uuid"] != user_uuid:
                            continue
                    if group_id != "*" and row["group_id"] != group_id:
                        continue
                    if scope == "session" and not event_name.startswith("session_"):
                        continue
                    if scope == "kernel" and not event_name.startswith("kernel_"):
                        continue
                    if session_id is not None:
                        if row["session_id"] != session_id:
                            continue
                    else:
                        if session_name != "*" and not (
                            (row["session_name"] == session_name)
                            and (row["access_key"] == access_key)
                        ):
                            continue
                    response_data = {
                        "reason": reason,
                        "sessionName": row["session_name"],
                        "ownerAccessKey": row["access_key"],
                        "sessionId": str(row["session_id"]),
                        "exitCode": exit_code,
                    }
                    if kernel_id := row.get("id"):
                        response_data["kernelId"] = str(kernel_id)
                    if cluster_role := row.get("cluster_role"):
                        response_data["clusterRole"] = cluster_role
                    if cluster_idx := row.get("cluster_idx"):
                        response_data["clusterIdx"] = cluster_idx
                    await resp.send(json.dumps(response_data), event=event_name)
                finally:
                    my_queue.task_done()
        finally:
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
    task_id = params["task_id"]
    access_key = request["keypair"]["access_key"]
    log.info("PUSH_BACKGROUND_TASK_EVENTS (ak:{}, t:{})", access_key, task_id)
    try:
        return await root_ctx.background_task_manager.push_bgtask_events(request, task_id)
    except ValueError as e:
        raise ObjectNotFound(extra_data=str(e), object_name="background task")


async def enqueue_kernel_creation_status_update(
    app: web.Application,
    source: AgentId,
    event: KernelPreparingEvent | KernelPullingEvent | KernelCreatingEvent | KernelStartedEvent,
) -> None:
    root_ctx: RootContext = app["_root.context"]
    app_ctx: PrivateContext = app["events.context"]

    async def _fetch():
        async with root_ctx.db.begin_readonly() as conn:
            query = (
                sa.select([
                    kernels.c.id,
                    kernels.c.session_id,
                    kernels.c.session_name,
                    kernels.c.access_key,
                    kernels.c.cluster_role,
                    kernels.c.cluster_idx,
                    kernels.c.domain_name,
                    kernels.c.group_id,
                    kernels.c.user_uuid,
                ])
                .select_from(kernels)
                .where(
                    (kernels.c.id == event.kernel_id),
                )
            )
            result = await conn.execute(query)
            return result.first()

    row = await execute_with_retry(_fetch)
    if row is None:
        return
    for q in app_ctx.session_event_queues:
        q.put_nowait((event.name, row._mapping, event.reason, None))


async def enqueue_kernel_termination_status_update(
    app: web.Application,
    agent_id: AgentId,
    event: KernelCancelledEvent | KernelTerminatingEvent | KernelTerminatedEvent,
) -> None:
    root_ctx: RootContext = app["_root.context"]
    app_ctx: PrivateContext = app["events.context"]

    async def _fetch():
        async with root_ctx.db.begin_readonly() as conn:
            query = (
                sa.select([
                    kernels.c.id,
                    kernels.c.session_id,
                    kernels.c.session_name,
                    kernels.c.access_key,
                    kernels.c.cluster_role,
                    kernels.c.cluster_idx,
                    kernels.c.domain_name,
                    kernels.c.group_id,
                    kernels.c.user_uuid,
                ])
                .select_from(kernels)
                .where(
                    (kernels.c.id == event.kernel_id),
                )
            )
            result = await conn.execute(query)
            return result.first()

    row = await execute_with_retry(_fetch)
    if row is None:
        return
    for q in app_ctx.session_event_queues:
        exit_code = (
            event.exit_code
            if isinstance(event, (KernelTerminatingEvent, KernelTerminatedEvent))
            else None
        )
        q.put_nowait((event.name, row._mapping, event.reason, exit_code))


async def enqueue_session_creation_status_update(
    app: web.Application,
    source: AgentId,
    event: (
        SessionEnqueuedEvent | SessionScheduledEvent | SessionStartedEvent | SessionCancelledEvent
    ),
) -> None:
    root_ctx: RootContext = app["_root.context"]
    app_ctx: PrivateContext = app["events.context"]

    async def _fetch() -> SessionRow | None:
        async with root_ctx.db.begin_readonly_session() as db_session:
            query = (
                sa.select(SessionRow)
                .where(SessionRow.id == event.session_id)
                .options(
                    load_only(
                        SessionRow.id,
                        SessionRow.name,
                        SessionRow.access_key,
                        SessionRow.domain_name,
                        SessionRow.group_id,
                        SessionRow.user_uuid,
                    )
                )
            )
            return await db_session.scalar(query)

    row = await execute_with_retry(_fetch)
    if row is None:
        return
    row_map = {
        "session_id": row.id,
        "session_name": row.name,
        "domain_name": row.domain_name,
        "user_uuid": row.user_uuid,
        "group_id": row.group_id,
        "access_key": row.access_key,
    }
    for q in app_ctx.session_event_queues:
        q.put_nowait((event.name, row_map, event.reason, None))


async def enqueue_session_termination_status_update(
    app: web.Application,
    agent_id: AgentId,
    event: SessionTerminatingEvent | SessionTerminatedEvent,
) -> None:
    root_ctx: RootContext = app["_root.context"]
    app_ctx: PrivateContext = app["events.context"]

    async def _fetch() -> SessionRow | None:
        async with root_ctx.db.begin_readonly_session() as db_session:
            query = (
                sa.select(SessionRow)
                .where(SessionRow.id == event.session_id)
                .options(
                    load_only(
                        SessionRow.id,
                        SessionRow.name,
                        SessionRow.access_key,
                        SessionRow.domain_name,
                        SessionRow.group_id,
                        SessionRow.user_uuid,
                    )
                )
            )
            return await db_session.scalar(query)

    row = await execute_with_retry(_fetch)
    if row is None:
        return
    row_map = {
        "session_id": row.id,
        "session_name": row.name,
        "domain_name": row.domain_name,
        "user_uuid": row.user_uuid,
        "group_id": row.group_id,
        "access_key": row.access_key,
    }
    for q in app_ctx.session_event_queues:
        q.put_nowait((event.name, row_map, event.reason, None))


async def enqueue_batch_task_result_update(
    app: web.Application,
    agent_id: AgentId,
    event: SessionSuccessEvent | SessionFailureEvent,
) -> None:
    root_ctx: RootContext = app["_root.context"]
    app_ctx: PrivateContext = app["events.context"]

    async def _fetch() -> SessionRow | None:
        async with root_ctx.db.begin_readonly_session() as db_session:
            query = (
                sa.select(SessionRow)
                .where(SessionRow.id == event.session_id)
                .options(
                    load_only(
                        SessionRow.id,
                        SessionRow.name,
                        SessionRow.access_key,
                        SessionRow.domain_name,
                        SessionRow.group_id,
                        SessionRow.user_uuid,
                    )
                )
            )
            return await db_session.scalar(query)

    row = await execute_with_retry(_fetch)
    if row is None:
        return
    row_map = {
        "session_id": row.id,
        "session_name": row.name,
        "domain_name": row.domain_name,
        "user_uuid": row.user_uuid,
        "group_id": row.group_id,
        "access_key": row.access_key,
    }
    for q in app_ctx.session_event_queues:
        q.put_nowait((event.name, row_map, event.reason, event.exit_code))


@attrs.define(slots=True, auto_attribs=True, init=False)
class PrivateContext:
    session_event_queues: Set[asyncio.Queue[Sentinel | SessionEventInfo]]


async def events_app_ctx(app: web.Application) -> AsyncIterator[None]:
    root_ctx: RootContext = app["_root.context"]
    app_ctx: PrivateContext = app["events.context"]
    app_ctx.session_event_queues = set()
    event_dispatcher: EventDispatcher = root_ctx.event_dispatcher
    event_dispatcher.subscribe(SessionEnqueuedEvent, app, enqueue_session_creation_status_update)
    event_dispatcher.subscribe(SessionScheduledEvent, app, enqueue_session_creation_status_update)
    event_dispatcher.subscribe(KernelPreparingEvent, app, enqueue_kernel_creation_status_update)
    event_dispatcher.subscribe(KernelPullingEvent, app, enqueue_kernel_creation_status_update)
    event_dispatcher.subscribe(KernelCreatingEvent, app, enqueue_kernel_creation_status_update)
    event_dispatcher.subscribe(KernelStartedEvent, app, enqueue_kernel_creation_status_update)
    event_dispatcher.subscribe(SessionStartedEvent, app, enqueue_session_creation_status_update)
    event_dispatcher.subscribe(
        KernelTerminatingEvent, app, enqueue_kernel_termination_status_update
    )
    event_dispatcher.subscribe(KernelTerminatedEvent, app, enqueue_kernel_termination_status_update)
    event_dispatcher.subscribe(KernelCancelledEvent, app, enqueue_kernel_termination_status_update)
    event_dispatcher.subscribe(
        SessionTerminatingEvent, app, enqueue_session_termination_status_update
    )
    event_dispatcher.subscribe(
        SessionTerminatedEvent, app, enqueue_session_termination_status_update
    )
    event_dispatcher.subscribe(SessionCancelledEvent, app, enqueue_session_creation_status_update)
    event_dispatcher.subscribe(SessionSuccessEvent, app, enqueue_batch_task_result_update)
    event_dispatcher.subscribe(SessionFailureEvent, app, enqueue_batch_task_result_update)
    root_ctx.background_task_manager.register_event_handlers(event_dispatcher)
    yield


async def events_shutdown(app: web.Application) -> None:
    # shutdown handler is called before waiting for closing active connections.
    # We need to put sentinels here to ensure delivery of them to active SSE connections.
    app_ctx: PrivateContext = app["events.context"]
    join_tasks = []
    for sq in app_ctx.session_event_queues:
        sq.put_nowait(sentinel)
        join_tasks.append(sq.join())
    await asyncio.gather(*join_tasks)


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
