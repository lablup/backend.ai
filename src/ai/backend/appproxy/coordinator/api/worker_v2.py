from __future__ import annotations

import dataclasses
import logging
import textwrap
import uuid
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Annotated, Iterable
from uuid import UUID

import aiohttp_cors
import attrs
from aiohttp import web
from dateutil.tz import tzutc
from pydantic import BaseModel, Field

from ai.backend.appproxy.common.config import get_default_redis_key_ttl
from ai.backend.appproxy.common.events import DoCheckWorkerLostEvent, WorkerLostEvent
from ai.backend.appproxy.common.exceptions import ObjectNotFound
from ai.backend.appproxy.common.types import (
    AppMode,
    CORSOptions,
    FrontendMode,
    ProxyProtocol,
    PydanticResponse,
    SerializableCircuit,
    WebMiddleware,
)
from ai.backend.appproxy.common.utils import (
    pydantic_api_handler,
    pydantic_api_response_handler,
)
from ai.backend.appproxy.coordinator.defs import LockID
from ai.backend.common.distributed import GlobalTimer
from ai.backend.common.events.dispatcher import EventHandler
from ai.backend.common.types import AgentId
from ai.backend.logging import BraceStyleAdapter

from ..models import Token, Worker, WorkerAppFilter, WorkerStatus
from ..models.utils import execute_with_txn_retry
from ..types import RootContext
from .types import CircuitListResponseModel, SlotModel, StubResponseModel
from .utils import auth_required

if TYPE_CHECKING:
    pass
    from sqlalchemy.ext.asyncio import AsyncSession as SASession

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


class WorkerModel(BaseModel):
    authority: Annotated[
        str,
        Field(
            description="authority string of worker. Unique across every workers joined on a single coordinator."
        ),
    ]
    frontend_mode: FrontendMode
    protocol: ProxyProtocol

    hostname: str
    tls_listen: bool
    tls_advertised: bool

    api_port: int

    port_range: Annotated[tuple[int, int] | None, Field(default=None)]
    wildcard_domain: Annotated[str | None, Field(default=None)]
    wildcard_traffic_port: Annotated[int | None, Field(default=None)]
    filtered_apps_only: bool
    traefik_last_used_marker_path: Annotated[str | None, Field(default=None)]

    accepted_traffics: list[AppMode]


class AppFilter(BaseModel):
    key: str
    value: str


class WorkerRequestModel(WorkerModel):
    app_filters: Annotated[list[AppFilter], Field(default=[])]


class WorkerResponseModel(WorkerModel):
    id: Annotated[UUID, Field(description="ID of worker.")]

    created_at: datetime
    updated_at: datetime

    available_slots: Annotated[
        int,
        Field(
            description=textwrap.dedent(
                """
                Number of slots worker is capable to hold. Workers serving `subdomain` frontend have -1 as `available_circuits`.
                For `port` frontend this value is number of ports exposed by the worker.
                """
            ),
        ),
    ]

    occupied_slots: Annotated[int, Field(description="Number of slots occupied by circuit.")]

    nodes: Annotated[
        int,
        Field(
            description="Number of actual nodes claiming as same worker. Can be considered as HA set up if this value is greater than 1.",
        ),
    ]

    slots: list[SlotModel]


class WorkerListResponseModel(BaseModel):
    workers: list[WorkerResponseModel]


class TokenResponseModel(BaseModel):
    login_session_token: str | None
    kernel_host: str
    kernel_port: int
    session_id: UUID
    user_uuid: UUID
    group_id: UUID
    access_key: str
    domain_name: str


@auth_required("worker")
@pydantic_api_response_handler
async def get_worker(request: web.Request) -> PydanticResponse[WorkerResponseModel]:
    """
    Returns information about worker mentioned.
    """
    root_ctx: RootContext = request.app["_root.context"]

    async with root_ctx.db.begin_readonly_session() as sess:
        worker = await Worker.get(sess, UUID(request.match_info["worker_id"]))
        return PydanticResponse(
            WorkerResponseModel(
                slots=[SlotModel(**dataclasses.asdict(s)) for s in await worker.list_slots(sess)],
                **worker.dump_model(),
            )
        )


@auth_required("worker")
@pydantic_api_response_handler
async def list_workers(request: web.Request) -> PydanticResponse[WorkerListResponseModel]:
    """
    Lists all workers recognized by coordinator.
    """
    root_ctx: RootContext = request.app["_root.context"]

    async with root_ctx.db.begin_readonly_session() as sess:
        workers = await Worker.list_workers(sess)
        return PydanticResponse(
            WorkerListResponseModel(
                workers=[
                    WorkerResponseModel(
                        slots=[
                            SlotModel(**dataclasses.asdict(s)) for s in await w.list_slots(sess)
                        ],
                        **w.dump_model(),
                    )
                    for w in workers
                ]
            )
        )


@auth_required("worker")
@pydantic_api_response_handler
async def list_worker_circuits(request: web.Request) -> PydanticResponse[CircuitListResponseModel]:
    """
    Lists every circuits worker is currently serving.
    """
    root_ctx: RootContext = request.app["_root.context"]

    async with root_ctx.db.begin_readonly_session() as sess:
        worker = await Worker.get(sess, UUID(request.match_info["worker_id"]), load_circuits=True)
        return PydanticResponse(
            CircuitListResponseModel(
                circuits=[SerializableCircuit(**c.dump_model()) for c in worker.circuits]
            )
        )


@auth_required("worker")
@pydantic_api_handler(WorkerRequestModel)
async def update_worker(
    request: web.Request, params: WorkerRequestModel
) -> PydanticResponse[WorkerResponseModel]:
    """
    Registers worker to coordinator.
    """

    root_ctx: RootContext = request.app["_root.context"]

    async def _update(sess: SASession) -> dict:
        try:
            worker = await Worker.find_by_authority(sess, params.authority)
            worker.frontend_mode = params.frontend_mode
            worker.protocol = params.protocol
            worker.hostname = params.hostname
            worker.tls_listen = params.tls_listen
            worker.tls_advertised = params.tls_advertised
            worker.api_port = params.api_port
            worker.port_range = params.port_range
            worker.wildcard_domain = params.wildcard_domain
            worker.wildcard_traffic_port = params.wildcard_traffic_port
            worker.filtered_apps_only = params.filtered_apps_only
            worker.traefik_last_used_marker_path = params.traefik_last_used_marker_path
            worker.updated_at = datetime.now()
            worker.nodes += 1
            worker.status = WorkerStatus.ALIVE
        except ObjectNotFound:
            worker = Worker.create(
                uuid.uuid4(),
                params.authority,
                params.frontend_mode,
                params.protocol,
                params.hostname,
                params.tls_listen,
                params.tls_advertised,
                params.api_port,
                params.accepted_traffics,
                port_range=params.port_range,
                wildcard_domain=params.wildcard_domain,
                wildcard_traffic_port=params.wildcard_traffic_port,
                filtered_apps_only=params.filtered_apps_only,
                traefik_last_used_marker_path=params.traefik_last_used_marker_path,
                status=WorkerStatus.ALIVE,
            )
            sess.add(worker)
            await sess.flush()
            await sess.refresh(worker)

        for filter in params.app_filters:
            try:
                await WorkerAppFilter.find_by_rule(sess, worker.id, filter.key, filter.value)
            except ObjectNotFound:
                filter_row = WorkerAppFilter.create(
                    uuid.uuid4(),
                    property_name=filter.key,
                    property_value=filter.value,
                    worker=worker.id,
                )
                sess.add(filter_row)

        result = dict(worker.dump_model())
        result["slots"] = [
            SlotModel(**dataclasses.asdict(s)) for s in (await worker.list_slots(sess))
        ]
        log.info("Worker {} joined", worker.authority)
        return result

    async with root_ctx.db.connect() as db_conn:
        result = await execute_with_txn_retry(_update, root_ctx.db.begin_session, db_conn)
    return PydanticResponse(WorkerResponseModel(**result))


@auth_required("worker")
@pydantic_api_response_handler
async def delete_worker(request: web.Request) -> PydanticResponse[StubResponseModel]:
    """
    Deassociates worker from coordinator.
    """
    root_ctx: RootContext = request.app["_root.context"]
    worker_id = UUID(request.match_info["worker_id"])

    async def _update(sess: SASession) -> None:
        worker = await Worker.get(sess, worker_id)
        worker.nodes -= 1
        if worker.nodes == 0:
            worker.status = WorkerStatus.LOST

    async with root_ctx.db.connect() as db_conn:
        await execute_with_txn_retry(_update, root_ctx.db.begin_session, db_conn)
    return PydanticResponse(StubResponseModel(success=True))


@auth_required("worker")
@pydantic_api_response_handler
async def heartbeat_worker(request: web.Request) -> PydanticResponse[WorkerResponseModel]:
    root_ctx: RootContext = request.app["_root.context"]
    worker_id = UUID(request.match_info["worker_id"])
    now = datetime.now(tzutc())

    async def _update(sess: SASession) -> dict:
        worker = await Worker.get(sess, worker_id)
        worker.updated_at = datetime.now()
        worker.status = WorkerStatus.ALIVE
        result = dict(worker.dump_model())
        result["slots"] = [
            SlotModel(**dataclasses.asdict(s)) for s in (await worker.list_slots(sess))
        ]

        # Update "last seen" timestamp for liveness tracking
        ttl = get_default_redis_key_ttl()
        await root_ctx.valkey_live.hset_with_expiry(
            "proxy-worker.last_seen",
            {worker.authority: str(now.timestamp())},
            ttl,
        )
        return result

    async with root_ctx.db.connect() as db_conn:
        result = await execute_with_txn_retry(_update, root_ctx.db.begin_session, db_conn)
    request["do_not_print_access_log"] = True
    return PydanticResponse(WorkerResponseModel(**result))


@auth_required("worker")
@pydantic_api_response_handler
async def get_token(request: web.Request) -> PydanticResponse[TokenResponseModel]:
    """
    Lists tokens issued within /v2/conf request handler.
    """
    root_ctx: RootContext = request.app["_root.context"]
    token_id = UUID(request.match_info["token_id"])

    async with root_ctx.db.begin_readonly_session() as sess:
        token = await Token.get(sess, token_id)
        return PydanticResponse(TokenResponseModel(**token.dump_model()))


async def check_worker_lost(
    app: web.Application, src: AgentId, event: DoCheckWorkerLostEvent
) -> None:
    root_ctx: RootContext = app["_root.context"]

    try:
        now = datetime.now(tzutc())
        timeout = timedelta(
            seconds=root_ctx.local_config.proxy_coordinator.worker_heartbeat_timeout
        )

        msg_data = await root_ctx.valkey_live.hgetall_str("proxy-worker.last_seen")

        async with root_ctx.db.begin_readonly_session() as sess:
            workers = await Worker.list_workers(sess)
            worker_map = {w.authority: w for w in workers}

        for worker_id_str, prev in msg_data.items():
            prev = datetime.fromtimestamp(float(prev), tzutc())
            if (
                (now - prev) > timeout
                and worker_id_str in worker_map
                and worker_map[worker_id_str].status == WorkerStatus.ALIVE
            ):
                await root_ctx.event_producer.anycast_event(
                    WorkerLostEvent(worker_id_str, "heartbeat timeout")
                )
    except Exception:
        log.exception("check_worker_lost(): exception:")


@attrs.define(slots=True, auto_attribs=True, init=False)
class PrivateContext:
    worker_lost_check_timer: GlobalTimer
    worker_lost_check_evh: EventHandler[web.Application, DoCheckWorkerLostEvent]


async def init(app: web.Application) -> None:
    root_ctx: RootContext = app["_root.context"]
    app_ctx: PrivateContext = app["worker.context"]

    # Scan ALIVE workers
    app_ctx.worker_lost_check_evh = root_ctx.event_dispatcher.consume(
        DoCheckWorkerLostEvent,
        app,
        check_worker_lost,
    )
    app_ctx.worker_lost_check_timer = GlobalTimer(
        root_ctx.distributed_lock_factory(LockID.LOCKID_WORKER_LOST, 15.0),
        root_ctx.event_producer,
        lambda: DoCheckWorkerLostEvent(),
        15.0,
        initial_delay=10.0,
        task_name="check_worker_lost_task",
    )
    await app_ctx.worker_lost_check_timer.join()


async def shutdown(app: web.Application) -> None:
    root_ctx: RootContext = app["_root.context"]
    app_ctx: PrivateContext = app["worker.context"]
    await app_ctx.worker_lost_check_timer.leave()
    root_ctx.event_dispatcher.unconsume(app_ctx.worker_lost_check_evh)


def create_app(
    default_cors_options: CORSOptions,
) -> tuple[web.Application, Iterable[WebMiddleware]]:
    app = web.Application()
    app["prefix"] = "api/worker"
    app["worker.context"] = PrivateContext()
    app.on_startup.append(init)
    app.on_shutdown.append(shutdown)
    cors = aiohttp_cors.setup(app, defaults=default_cors_options)
    add_route = app.router.add_route
    root_resource = cors.add(app.router.add_resource(r""))
    cors.add(root_resource.add_route("GET", list_workers))
    cors.add(root_resource.add_route("PUT", update_worker))
    cors.add(add_route("GET", "/{worker_id}", get_worker))
    cors.add(add_route("PATCH", "/{worker_id}", heartbeat_worker))
    cors.add(add_route("GET", "/{worker_id}/circuits", list_worker_circuits))
    cors.add(add_route("DELETE", "/{worker_id}", delete_worker))
    return app, []
