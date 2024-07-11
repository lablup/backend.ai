from __future__ import annotations

import asyncio
import json
import logging
import uuid
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncIterator,
    Final,
    Iterable,
    Mapping,
    NamedTuple,
    Tuple,
    Union,
    cast,
)

import aiohttp_cors
import attrs
import sqlalchemy as sa
import trafaret as t
from aiohttp import web
from aiohttp_sse import sse_response
from aiotools import adefer
from sqlalchemy.ext.asyncio import AsyncSession as SASession
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
from ai.backend.common.json import ExtendedJSONEncoder
from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common.types import AccessKey, AgentId, KernelId, SessionId

from ..models import UserRole
from ..models.group import GroupRow
from ..models.kernel import KernelRow
from ..models.session import SessionRow
from ..models.utils import execute_with_txn_retry
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


class SessionEventInfo(NamedTuple):
    event_name: str
    row: SessionRow
    reason: str
    exit_code: int | None


class KernelEventInfo(NamedTuple):
    event_name: str
    row: KernelRow
    reason: str
    exit_code: int | None


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
    my_queue: asyncio.Queue[Sentinel | SessionEventInfo | KernelEventInfo] = asyncio.Queue()
    log.info("PUSH_SESSION_EVENTS (ak:{}, s:{}, g:{})", access_key, session_name, group_name)
    group_id: uuid.UUID | str
    if group_name == "*":
        group_id = "*"
    else:
        async with root_ctx.db.begin_readonly_session() as db_session:
            query = sa.select(GroupRow).where(GroupRow.name == group_name)
            row = cast(GroupRow | None, (await db_session.scalars(query)).first())
            if row is None:
                raise GroupNotFound
            group_id = row.id
    app_ctx.session_event_queues.add(my_queue)
    defer(lambda: app_ctx.session_event_queues.remove(my_queue))
    async with sse_response(request) as resp:
        try:
            while True:
                evdata = await my_queue.get()
                try:
                    match evdata:
                        case Sentinel():
                            break
                        case SessionEventInfo(event_name, row, reason, exit_code):
                            if scope == "kernel":
                                continue
                            kernel_id = None
                            cluster_role = None
                            cluster_idx = None
                            row_session_name = cast(str, row.name)
                            row_session_id = cast(SessionId, row.id)
                            row_ak = cast(AccessKey, row.access_key)
                            row_domain_name = cast(str, row.domain_name)
                            row_user_id = cast(uuid.UUID, row.user_uuid)
                            row_group_id = cast(uuid.UUID, row.group_id)
                        case KernelEventInfo(event_name, row, reason, exit_code):
                            if scope == "session":
                                continue
                            kernel_id = cast(KernelId, row.id)
                            cluster_role = cast(str, row.cluster_role)
                            cluster_idx = cast(int, row.cluster_idx)
                            row_session_name = cast(str, row.session_name)
                            row_session_id = cast(SessionId, row.session_id)
                            row_ak = cast(AccessKey, row.access_key)
                            row_domain_name = cast(str, row.domain_name)
                            row_user_id = cast(uuid.UUID, row.user_uuid)
                            row_group_id = cast(uuid.UUID, row.group_id)
                    if user_role in (UserRole.USER, UserRole.ADMIN):
                        if row_domain_name != request["user"]["domain_name"]:
                            continue
                    if user_role == UserRole.USER and row_user_id != user_uuid:
                        continue
                    if group_id != "*" and row_group_id != group_id:
                        continue
                    if session_id is not None:
                        if row_session_id != session_id:
                            continue
                    else:
                        if session_name != "*" and (
                            row_session_name != session_name or row_ak != access_key
                        ):
                            continue
                    response_data = {
                        "reason": reason,
                        "sessionName": row_session_name,
                        "ownerAccessKey": row_ak,
                        "sessionId": row_session_id,
                        "exitCode": exit_code,
                    }
                    if kernel_id is not None:
                        response_data["kernelId"] = kernel_id
                    if cluster_role is not None:
                        response_data["clusterRole"] = cluster_role
                    if cluster_idx is not None:
                        response_data["clusterIdx"] = cluster_idx
                    await resp.send(
                        json.dumps(response_data, cls=ExtendedJSONEncoder), event=event_name
                    )
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

    async def _fetch(db_session: SASession) -> KernelRow | None:
        query = (
            sa.select(KernelRow)
            .where(KernelRow.id == event.kernel_id)
            .options(
                load_only(
                    KernelRow.id,
                    KernelRow.session_id,
                    KernelRow.session_name,
                    KernelRow.access_key,
                    KernelRow.cluster_role,
                    KernelRow.cluster_idx,
                    KernelRow.domain_name,
                    KernelRow.group_id,
                    KernelRow.user_uuid,
                )
            )
        )
        return await db_session.scalar(query)

    async with root_ctx.db.connect() as db_conn:
        row = await execute_with_txn_retry(_fetch, root_ctx.db.begin_readonly_session, db_conn)
    if row is None:
        return
    for q in app_ctx.session_event_queues:
        q.put_nowait(KernelEventInfo(event.name, row, event.reason, None))


async def enqueue_kernel_termination_status_update(
    app: web.Application,
    agent_id: AgentId,
    event: KernelCancelledEvent | KernelTerminatingEvent | KernelTerminatedEvent,
) -> None:
    root_ctx: RootContext = app["_root.context"]
    app_ctx: PrivateContext = app["events.context"]

    async def _fetch(db_session: SASession) -> KernelRow | None:
        query = (
            sa.select(KernelRow)
            .where(KernelRow.id == event.kernel_id)
            .options(
                load_only(
                    KernelRow.id,
                    KernelRow.session_id,
                    KernelRow.session_name,
                    KernelRow.access_key,
                    KernelRow.cluster_role,
                    KernelRow.cluster_idx,
                    KernelRow.domain_name,
                    KernelRow.group_id,
                    KernelRow.user_uuid,
                )
            )
        )
        return await db_session.scalar(query)

    async with root_ctx.db.connect() as db_conn:
        row = await execute_with_txn_retry(_fetch, root_ctx.db.begin_readonly_session, db_conn)
    if row is None:
        return
    for q in app_ctx.session_event_queues:
        exit_code = (
            event.exit_code
            if isinstance(event, (KernelTerminatingEvent, KernelTerminatedEvent))
            else None
        )
        q.put_nowait(KernelEventInfo(event.name, row, event.reason, exit_code))


async def enqueue_session_creation_status_update(
    app: web.Application,
    source: AgentId,
    event: (
        SessionEnqueuedEvent | SessionScheduledEvent | SessionStartedEvent | SessionCancelledEvent
    ),
) -> None:
    root_ctx: RootContext = app["_root.context"]
    app_ctx: PrivateContext = app["events.context"]

    async def _fetch(db_session: SASession) -> SessionRow | None:
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

    async with root_ctx.db.connect() as db_conn:
        row = await execute_with_txn_retry(_fetch, root_ctx.db.begin_readonly_session, db_conn)
    if row is None:
        return
    for q in app_ctx.session_event_queues:
        q.put_nowait(SessionEventInfo(event.name, row, event.reason, None))


async def enqueue_session_termination_status_update(
    app: web.Application,
    agent_id: AgentId,
    event: SessionTerminatingEvent | SessionTerminatedEvent,
) -> None:
    root_ctx: RootContext = app["_root.context"]
    app_ctx: PrivateContext = app["events.context"]

    async def _fetch(db_session: SASession) -> SessionRow | None:
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

    async with root_ctx.db.connect() as db_conn:
        row = await execute_with_txn_retry(_fetch, root_ctx.db.begin_readonly_session, db_conn)
    if row is None:
        return
    for q in app_ctx.session_event_queues:
        q.put_nowait(SessionEventInfo(event.name, row, event.reason, None))


async def enqueue_batch_task_result_update(
    app: web.Application,
    agent_id: AgentId,
    event: SessionSuccessEvent | SessionFailureEvent,
) -> None:
    root_ctx: RootContext = app["_root.context"]
    app_ctx: PrivateContext = app["events.context"]

    async def _fetch(db_session: SASession) -> SessionRow | None:
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

    async with root_ctx.db.connect() as db_conn:
        row = await execute_with_txn_retry(_fetch, root_ctx.db.begin_readonly_session, db_conn)
    if row is None:
        return
    for q in app_ctx.session_event_queues:
        q.put_nowait(SessionEventInfo(event.name, row, event.reason, event.exit_code))


@attrs.define(slots=True, auto_attribs=True, init=False)
class PrivateContext:
    session_event_queues: set[asyncio.Queue[Sentinel | SessionEventInfo | KernelEventInfo]]


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
