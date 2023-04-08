import asyncio
import json
import logging
import secrets
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, Iterable, Mapping, MutableMapping, Sequence, Tuple, Union
from urllib.parse import urlparse

import aiohttp_cors
import aiotools
import attrs
import sqlalchemy as sa
import trafaret as t
from aiohttp import ClientSession, web
from async_timeout import timeout
from dateutil.parser import isoparse
from dateutil.tz import tzutc

from ai.backend.common import validators as tx
from ai.backend.common.docker import ImageRef, validate_image_labels
from ai.backend.common.events import SessionCancelledEvent, SessionStartedEvent
from ai.backend.common.exception import AliasResolutionFailed, UnknownImageReference
from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common.types import AgentId, ClusterMode, ServicePort, SessionTypes
from ai.backend.common.utils import cancel_tasks, str_to_timedelta

from ..defs import DEFAULT_IMAGE_ARCH, DEFAULT_ROLE
from ..models import (
    ImageRow,
    KernelRow,
    UserRole,
    domains,
    query_bootstrap_script,
    verify_vfolder_name,
    vfolders,
)
from ..models.endpoint import EndpointRow
from ..models.kernel import KernelStatus
from ..models.routing import RoutingRow
from ..models.session import SessionRow, SessionStatus
from ..models.utils import ExtendedAsyncSAEngine
from ..types import UserScope
from .auth import auth_required
from .exceptions import (
    AppNotFound,
    BackendError,
    EndpointNotFound,
    ImageNotFound,
    InsufficientPrivilege,
    InternalServerError,
    InvalidAPIParameters,
    ServicePortNotFound,
    ServiceUnavailable,
    SessionNotFound,
    TooManySessionsMatched,
    UnknownImageReferenceError,
)
from .manager import ALL_ALLOWED, READ_ALLOWED, server_status_required
from .scaling_group import query_wsproxy_status
from .types import CORSOptions, WebMiddleware
from .utils import check_api_params, get_access_key_scopes, undefined

if TYPE_CHECKING:
    from .context import RootContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


class UndefChecker(t.Trafaret):
    def check_and_return(self, value: Any) -> object:
        if value == undefined:
            return value
        else:
            self._failure("Invalid Undef format", value=value)
            return None


@auth_required
@server_status_required(READ_ALLOWED)
@check_api_params(
    t.Dict(
        {
            tx.AliasedKey(["project_id", "projectId"]): tx.UUID,
        }
    ),
)
async def list_(request: web.Request, params: Any) -> web.Response:
    root_ctx: RootContext = request.app["_root.context"]
    access_key = request["keypair"]["access_key"]
    project_id = params["project_id"]

    log.info("SERVICE.LIST (email:{}, ak:{})", request["user"]["email"], access_key)

    async with root_ctx.db.begin_readonly_session() as db_sess:
        j = sa.join(SessionRow, RoutingRow, SessionRow.id == RoutingRow.session).join(
            EndpointRow, RoutingRow.endpoint == EndpointRow.id
        )
        query = (
            sa.select(
                SessionRow.id,
                SessionRow.name,
                SessionRow.status,
            )
            .select_from(j)
            .where(SessionRow.group_id == project_id)
        )
        result = await db_sess.execute(query)
        rows = result.scalars().all()

    return web.json_response(rows, status=200)


@auth_required
@server_status_required(READ_ALLOWED)
@check_api_params(
    t.Dict(
        {
            tx.AliasedKey(["endpoint_id", "endpointId"]): tx.UUID,
        }
    ),
)
async def get_info(request: web.Request, params: Any) -> web.Response:
    root_ctx: RootContext = request.app["_root.context"]
    access_key = request["keypair"]["access_key"]

    log.info("SERVICE.GET_INFO (email:{}, ak:{})", request["user"]["email"], access_key)

    async with root_ctx.db.begin_readonly_session() as db_sess:
        j = sa.join(SessionRow, RoutingRow, SessionRow.id == RoutingRow.session).join(
            EndpointRow, RoutingRow.endpoint == EndpointRow.id
        )
        query = (
            sa.select(
                SessionRow.id,
                SessionRow.name,
                SessionRow.status,
                EndpointRow.image,
                EndpointRow.model,
                EndpointRow.url,
            )
            .select_from(j)
            .where(RoutingRow.endpoint == params["endpoint_id"])
        )
        result = await db_sess.execute(query)
        rows = result.scalars().all()

    return web.json_response(rows, status=200)


@auth_required
@server_status_required(ALL_ALLOWED)
@check_api_params(
    t.Dict(
        {
            tx.AliasedKey(["endpoint_id", "endpointId"]): tx.UUID,
            tx.AliasedKey(["service_name", "serviceName"]): t.String,
            tx.AliasedKey(["model_id", "modelId"]): tx.UUID,
            tx.AliasedKey(["model_version", "modelVersion"]): t.String,
            tx.AliasedKey(["image_ref", "imageRef"]): t.String,
            tx.AliasedKey(["arch", "architecture"], default=DEFAULT_IMAGE_ARCH)
            >> "architecture": t.String,
            tx.AliasedKey(
                ["group", "groupName", "group_name", "project", "project_name", "projectName"],
                default="default",
            ): t.String,
            tx.AliasedKey(["domain", "domainName", "domain_name"], default="default"): t.String,
            tx.AliasedKey(["resource_opts", "resourceOpts"], default=dict): t.Mapping(
                t.String, t.Any
            ),
            tx.AliasedKey(["cluster_size", "clusterSize"], default=1): t.ToInt[1:],
            tx.AliasedKey(["cluster_mode", "clusterMode"], default="single-node"): tx.Enum(
                ClusterMode
            ),
            t.Key("tag", default=None): t.Null | t.String,
            t.Key("config", default=dict): t.Mapping(t.String, t.Any),
            t.Key("enqueue_only", default=False): t.ToBool,
            t.Key("max_wait_seconds", default=0): t.Int[0:],
        }
    ),
)
async def create(request: web.Request, params: Any) -> web.Response:
    from .session import query_userinfo

    root_ctx: RootContext = request.app["_root.context"]
    app_ctx: PrivateContext = request.app["service.context"]
    access_key = request["keypair"]["access_key"]
    domain_name = request["user"]["domain_name"]
    user_role = request["user"]["role"]
    model_id = params["model_id"]
    model_version = params["model_version"]

    params["owner_access_key"] = access_key
    async with root_ctx.db.begin_readonly() as db_conn:
        owner_uuid, group_id, resource_policy = await query_userinfo(request, params, db_conn)

    log.info("SERVICE.CREATE (email:{}, ak:{})", request["user"]["email"], access_key)
    resp: MutableMapping[str, Any] = {}
    current_task = asyncio.current_task()
    assert current_task is not None

    # Resolve the image reference.
    try:
        async with root_ctx.db.begin_readonly_session() as session:
            image_row = await ImageRow.resolve(
                session,
                [
                    ImageRef(params["image_ref"], ["*"], params["architecture"]),
                    params["image_ref"],
                ],
            )
        requested_image_ref = image_row.image_ref
        parsed_labels: dict[str, Any] = validate_image_labels(image_row.labels)
        try:
            model_mount_path = parsed_labels["ai.backend.model-path"]
        except KeyError:
            raise InvalidAPIParameters("Given image does not have model-path label")
        # service_ports: dict[str, ServicePort] = {
        #     item["name"]: item for item in parsed_labels["ai.backend.service-ports"]
        # }
        endpoint_ports: Sequence[str] = parsed_labels["ai.backend.endpoint-ports"]
        endpoint_port_name = endpoint_ports[0]
        # TODO: use endpoints & service_ports to populate the routing table
        async with root_ctx.db.begin_readonly_session() as db_sess:
            query = sa.select([domains.c.allowed_docker_registries]).where(
                domains.c.name == params["domain"]
            )
            allowed_registries = await db_sess.scalar(query)
            if requested_image_ref.registry not in allowed_registries:
                raise AliasResolutionFailed
    except AliasResolutionFailed:
        raise ImageNotFound("unknown alias or disallowed registry")

    # Check work directory and reserved name directory.
    mount_map = params["config"].get("mount_map", {})
    if mount_map is not None:
        original_folders = mount_map.keys()
        alias_folders = mount_map.values()
        if len(alias_folders) != len(set(alias_folders)):
            raise InvalidAPIParameters("Duplicate alias folder name exists.")

        alias_name: str
        for alias_name in alias_folders:
            if alias_name is None:
                continue
            if alias_name.startswith("/home/work/"):
                alias_name = alias_name.replace("/home/work/", "")
            if alias_name == "":
                raise InvalidAPIParameters("Alias name cannot be empty.")
            if alias_name == model_mount_path:
                raise InvalidAPIParameters(
                    f"Alias name cannot be the same with model path: `{model_mount_path}`"
                )
            if not verify_vfolder_name(alias_name):
                raise InvalidAPIParameters(str(alias_name) + " is reserved for internal path.")
            if alias_name in original_folders:
                raise InvalidAPIParameters(
                    f"Alias name cannot be set to an existing folder name: {alias_name}"
                )

    # Append model mount path
    mounts: list[str] = params["config"].get("mounts", [])
    async with root_ctx.db.begin_readonly() as db_conn:
        query = sa.select([vfolders.c.name]).where(vfolders.c.id == model_id)
        result = await db_conn.execute(query)
        vfolder_name = result.first()["name"]
    model_path = f"{vfolder_name}/versions/{model_version}"
    mounts = [*mounts, model_path]
    mount_map = {
        **mount_map,
        model_path: model_mount_path,
    }
    params["config"]["mounts"] = mounts
    params["config"]["mount_map"] = mount_map

    endpoint_id = params["endpoint_id"]

    starts_at: Union[datetime, None] = None
    if params["starts_at"]:
        try:
            starts_at = isoparse(params["starts_at"])
        except ValueError:
            _td = str_to_timedelta(params["starts_at"])
            starts_at = datetime.now(tzutc()) + _td

    # TODO: consider clustered inference session
    if params["cluster_size"] > 1:
        log.debug(" -> cluster_mode:{} (replicate)", params["cluster_mode"])

    session_creation_id = secrets.token_urlsafe(16)
    start_event = asyncio.Event()
    service_creation_tracker = app_ctx.service_creation_tracker
    service_creation_tracker[session_creation_id] = start_event

    async with root_ctx.db.begin_readonly() as conn:
        # Use keypair bootstrap_script if it is not delivered as a parameter
        if not params["bootstrap_script"]:
            script, _ = await query_bootstrap_script(conn, access_key)
            params["bootstrap_script"] = script

    # creation_config = {
    #     **params["config"],
    #     "endpoint_id": endpoint_id,
    # }
    try:
        session_id = await asyncio.shield(
            app_ctx.database_ptask_group.create_task(
                root_ctx.registry.enqueue_session(
                    session_creation_id,
                    params["service_name"],
                    access_key,
                    {
                        "creation_config": params["config"],
                        "kernel_configs": [
                            {
                                "image_ref": requested_image_ref,
                                "cluster_role": DEFAULT_ROLE,
                                "cluster_idx": 1,
                                "local_rank": 0,
                                "cluster_hostname": f"{DEFAULT_ROLE}1",
                                "creation_config": params["config"],
                                "bootstrap_script": params["bootstrap_script"],
                                "startup_command": params["startup_command"],
                            }
                        ],
                    },
                    params["config"]["scaling_group"],
                    SessionTypes.INFERENCE,
                    resource_policy,
                    user_scope=UserScope(
                        domain_name=domain_name,
                        group_id=group_id,
                        user_uuid=owner_uuid,
                        user_role=user_role,
                    ),
                    cluster_mode=params["cluster_mode"],
                    cluster_size=params["cluster_size"],
                    session_tag=params["tag"],
                    starts_at=starts_at,
                    agent_list=params["config"]["agent_list"],
                    dependency_sessions=params["dependencies"],
                )
            ),
        )

        resp["servicePorts"] = []
        app_ctx.pending_waits.add(current_task)
        max_wait = params["max_wait_seconds"]
        try:
            if max_wait > 0:
                with timeout(max_wait):
                    await start_event.wait()
            else:
                await start_event.wait()
        except asyncio.TimeoutError:
            resp["status"] = "TIMEOUT"
        else:
            await asyncio.sleep(0.5)
            async with root_ctx.db.begin_readonly_session() as db_sess:
                query = sa.select(KernelRow.status, KernelRow.service_ports).where(
                    (KernelRow.session_id == session_id) & (KernelRow.cluster_role == DEFAULT_ROLE)
                )
                result = await db_sess.execute(query)
                row = result.first()
            resp["status"] = row.status.name
            endpoint_host_port = None
            if row.status == KernelStatus.RUNNING:
                for item in row.service_ports:
                    response_dict = {
                        "name": item["name"],
                        "protocol": item["protocol"],
                        "ports": item["container_ports"],
                    }
                    if "url_template" in item:
                        response_dict["url_template"] = item["url_template"]
                    if "allowed_arguments" in item:
                        response_dict["allowed_arguments"] = item["allowed_arguments"]
                    if "allowed_envs" in item:
                        response_dict["allowed_envs"] = item["allowed_envs"]
                    resp["servicePorts"].append(response_dict)

                    if item["name"] == endpoint_port_name:
                        endpoint_host_port = item["host_ports"][0]

            if endpoint_host_port is None:
                raise InternalServerError(
                    extra_msg=f"Service port with name `{endpoint_port_name}` not found"
                )

            # Create the routing between the inference session and the endpoint
            await RoutingRow.create(
                root_ctx.db,
                endpoint_id,
                session_id=session_id,
                model_id=model_id,
                model_version=model_version,
                # TODO: get the preopen host-side port number
                session_endpoint_name=endpoint_port_name,
                session_endpoint_port=endpoint_host_port,
                traffic_ratio=1.0,
            )

        resp["sessionId"] = str(session_id)  # changed since API v5
        resp["sessionName"] = str(params["service_name"])
        resp["status"] = SessionStatus.PENDING.name
        resp["endpointHostPort"] = endpoint_host_port
        resp["endpointPortName"] = endpoint_port_name
        resp["created"] = True
    except asyncio.CancelledError:
        raise
    except BackendError:
        log.exception("GET_OR_CREATE: exception")
        raise
    except UnknownImageReference:
        raise UnknownImageReferenceError(f"Unknown image reference: {params['image']}")
    except Exception:
        log.exception("GET_OR_CREATE: unexpected error!")
        raise InternalServerError
    finally:
        app_ctx.pending_waits.discard(current_task)
        del service_creation_tracker[session_creation_id]
    return web.json_response(resp, status=201)


async def handle_service_kernel_creation(
    db_engine: ExtendedAsyncSAEngine,
    endpoint_id: uuid.UUID,
    session_id: uuid.UUID,
    kernel_id: uuid.UUID,
    *,
    service_ports: Sequence[ServicePort],
) -> None:
    async def _populate_service_port() -> ServicePort:
        async with db_engine.begin_readonly_session() as db_session:
            query = sa.select(KernelRow.image).where(KernelRow.id == kernel_id)
            image_name = await db_session.scalar(query)
            image_row = await ImageRow.resolve(
                db_session,
                [
                    ImageRef(image_name),
                ],
            )
            parsed_labels: dict[str, Any] = validate_image_labels(image_row.labels)
            # service_ports: dict[str, ServicePort] = {item["name"]: item for item in parsed_labels["ai.backend.service-ports"]}
            endpoints: Sequence[str] = parsed_labels["ai.backend.endpoint-ports"]

        for eport in endpoints:
            for sport in service_ports:
                if int(eport) in sport["container_ports"]:
                    return sport
        raise ServicePortNotFound()

    sport = await _populate_service_port()
    async with db_engine.begin_session() as db_sess:
        query = (
            sa.update(RoutingRow)
            .where((RoutingRow.endpoint_id == endpoint_id) & (RoutingRow.session_id == session_id))
            .values(
                session_endpoint_name=sport["name"],
                session_endpoint_port=sport["container_ports"][0],
            )
        )
        await db_sess.execute(query)
    return None


@auth_required
@server_status_required(READ_ALLOWED)
@check_api_params(
    t.Dict(
        {
            t.Key("login_session_token", default=None): t.Null | t.String,
            tx.AliasedKey(["service_id", "serviceId"]): tx.UUID | t.String,
            tx.AliasedKey(["port"], default=None): t.Null | t.Int[1024:65535],
            tx.AliasedKey(["envs"], default=None): t.Null | t.String,  # stringified JSON
            # e.g., '{"PASSWORD": "12345"}'
            tx.AliasedKey(["arguments"], default=None): t.Null | t.String,  # stringified JSON
            # e.g., '{"-P": "12345"}'
            # The value can be one of:
            # None, str, List[str]
        }
    ),
)
async def start(request: web.Request, params: Any) -> web.Response:
    root_ctx: RootContext = request.app["_root.context"]
    app_ctx: PrivateContext = request.app["session.context"]
    service_id = params["service_id"]
    access_key = request["keypair"]["access_key"]
    # service_name = "inference"

    log.info("SERVICE.START (email:{}, ak:{})", request["user"]["email"], access_key)

    try:
        async with root_ctx.db.begin_readonly_session() as db_sess:
            service_session = await SessionRow.get_session_to_start_service(
                db_sess, service_id, access_key
            )
            routing_query = sa.select(
                RoutingRow.session_endpoint_name, RoutingRow.session_endpoint_port
            ).where(RoutingRow.session_id == service_id)
            # There can be multiple routing rows with single service_id, but we assume there is only one routing so far.
            routing = (await db_sess.scalars(routing_query)).first()
            service_name = routing.session_endpoint_name
            # service_host_port = routing.session_endpoint_port
    except (SessionNotFound, TooManySessionsMatched):
        raise

    main_kernel: KernelRow = service_session.main_kernel
    wsproxy_addr = service_session.scaling_group.wsproxy_addr
    if not wsproxy_addr:
        raise ServiceUnavailable("No coordinator configured for this resource group")
    wsproxy_status = await query_wsproxy_status(wsproxy_addr)
    if advertise_addr := wsproxy_status.get("advertise_address"):
        wsproxy_advertise_addr = advertise_addr
    else:
        wsproxy_advertise_addr = wsproxy_addr

    if main_kernel.kernel_host is None:
        kernel_host = urlparse(main_kernel.agent_addr).hostname
    else:
        kernel_host = main_kernel.kernel_host
    for sport in main_kernel.service_ports:
        if sport["name"] == service_name:
            if params["port"]:
                # using one of the primary/secondary ports of the app
                try:
                    hport_idx = sport["container_ports"].index(params["port"])
                except ValueError:
                    raise InvalidAPIParameters(
                        f"Service {service_name} does not open the port number {params['port']}."
                    )
                host_port = sport["host_ports"][hport_idx]
            else:
                # using the default (primary) port of the app
                if "host_ports" not in sport:
                    host_port = sport["host_port"]  # legacy kernels
                else:
                    host_port = sport["host_ports"][0]
            break
    else:
        raise AppNotFound(f"{service_session.name}:{service_name}")

    await asyncio.shield(
        app_ctx.database_ptask_group.create_task(
            root_ctx.registry.increment_session_usage(service_session),
        )
    )

    opts: MutableMapping[str, Union[None, str, list[str]]] = {}
    if params["arguments"] is not None:
        opts["arguments"] = json.loads(params["arguments"])
    if params["envs"] is not None:
        opts["envs"] = json.loads(params["envs"])

    result: Mapping[str, Any] = await asyncio.shield(
        app_ctx.rpc_ptask_group.create_task(
            root_ctx.registry.start_service(service_session, service_name, opts),
        ),
    )
    if result["status"] == "failed":
        raise InternalServerError("Failed to launch the app service", extra_data=result["error"])

    async with ClientSession() as session:
        async with session.post(
            f"{wsproxy_addr}/v2/conf",
            json={
                "login_session_token": params["login_session_token"],
                "kernel_host": kernel_host,
                "kernel_port": host_port,
            },
        ) as resp:
            token_json = await resp.json()
            return web.json_response(
                {
                    "token": token_json["token"],
                    "wsproxy_addr": wsproxy_advertise_addr,
                }
            )


@auth_required
@server_status_required(READ_ALLOWED)
@check_api_params(
    t.Dict(
        {
            tx.AliasedKey(["service_id", "serviceId"]): tx.UUID | t.String,
        }
    ),
)
async def stop(request: web.Request, params: Any) -> web.Response:
    access_key = request["keypair"]["access_key"]

    log.info("SERVICE.STOP (email:{}, ak:{})", request["user"]["email"], access_key)
    return web.Response(status=204)


@auth_required
@server_status_required(READ_ALLOWED)
@check_api_params(
    t.Dict(
        {
            tx.AliasedKey(["endpoint_id", "endpointId"]): tx.UUID | t.String,
            tx.AliasedKey(["input_args", "inputArgs"], default=dict): t.Mapping(t.String, t.Any),
            tx.AliasedKey(["force_route", "forceRoute"], default=None): tx.UUID | t.Null,
            # the request body can be an arbitrary binary blob.
        }
    ),
)
async def invoke(request: web.Request, params: Any) -> web.StreamResponse:
    root_ctx: RootContext = request.app["_root.context"]
    access_key = request["keypair"]["access_key"]
    force_route = params["force_route"]
    endpoint_id = params["endpoint_id"]

    log.info("SERVICE.INVOKE (email:{}, ak:{})", request["user"]["email"], access_key)

    # TODO: get the first attached endpoint and routing info
    #       If force_route is given, use that route.
    async with root_ctx.db.begin_readonly_session() as db_session:
        endpoint_row: EndpointRow = await db_session.get(EndpointRow, uuid.UUID(endpoint_id))
        if endpoint_row is None:
            raise EndpointNotFound()
        url: str = endpoint_row.url
        if force_route is not None:
            routing = await RoutingRow.get(db_session, force_route)
        else:
            query = sa.select(RoutingRow).where(RoutingRow.endpoint_id == endpoint_id)
            routing = (await db_session.scalars(query)).first()
        endpoint_port = routing.session_endpoint_port

    # TODO: make a direct HTTP request to the container's endpoint port.
    async with ClientSession() as session:
        async with session.get(f"{url}:{endpoint_port}") as resp:
            status = resp.status
    return web.Response(status=status)


@auth_required
@server_status_required(READ_ALLOWED)
@check_api_params(
    t.Dict(
        {
            tx.AliasedKey(["service_id", "serviceId"]): tx.UUID,
        }
    ),
)
async def delete(request: web.Request, params: Any) -> web.Response:
    root_ctx: RootContext = request.app["_root.context"]
    access_key = request["keypair"]["access_key"]
    # session_name = request.match_info["session_name"]
    service_id = params["service_id"]

    log.info("SERVICE.DELETE (email:{}, ak:{})", request["user"]["email"], access_key)

    requester_access_key, owner_access_key = await get_access_key_scopes(request, params)
    if requester_access_key != owner_access_key and request["user"]["role"] not in (
        UserRole.ADMIN,
        UserRole.SUPERADMIN,
    ):
        raise InsufficientPrivilege("You are not allowed to delete others's services")

    async with root_ctx.db.begin_session() as db_sess:
        # Delete endpoint first
        await db_sess.execute(sa.delete(EndpointRow).where(session=service_id))

        session = await SessionRow.get_session_with_kernels(service_id, db_session=db_sess)
    last_stat = await root_ctx.registry.destroy_session(
        session,
    )
    resp = {
        "stats": last_stat,
    }
    return web.json_response(resp, status=200)


async def handle_service_creation_lifecycle(
    app: web.Application,
    source: AgentId,
    event: SessionStartedEvent | SessionCancelledEvent,
) -> None:
    """
    Update the database according to the session-level lifecycle events
    published by the manager.
    """
    app_ctx: PrivateContext = app["service.context"]
    if event.creation_id not in app_ctx.service_creation_tracker:
        return
    log.debug("handle_session_creation_lifecycle: ev:{} s:{}", event.name, event.session_id)
    if isinstance(event, SessionStartedEvent):
        if tracker := app_ctx.service_creation_tracker.get(event.creation_id):
            tracker.set()
    elif isinstance(event, SessionCancelledEvent):
        if tracker := app_ctx.service_creation_tracker.get(event.creation_id):
            tracker.set()


@attrs.define(slots=True, auto_attribs=True, init=False)
class PrivateContext:
    service_creation_tracker: dict[str, asyncio.Event]
    database_ptask_group: aiotools.PersistentTaskGroup
    rpc_ptask_group: aiotools.PersistentTaskGroup
    pending_waits: set[asyncio.Task[None]]


async def init(app: web.Application) -> None:
    app_ctx: PrivateContext = app["service.context"]
    app_ctx.database_ptask_group = aiotools.PersistentTaskGroup()
    app_ctx.rpc_ptask_group = aiotools.PersistentTaskGroup()
    app_ctx.service_creation_tracker = {}
    app_ctx.pending_waits = set()


async def shutdown(app: web.Application) -> None:
    app_ctx: PrivateContext = app["service.context"]
    await app_ctx.database_ptask_group.shutdown()
    await app_ctx.rpc_ptask_group.shutdown()
    await cancel_tasks(app_ctx.pending_waits)


def create_app(
    default_cors_options: CORSOptions,
) -> Tuple[web.Application, Iterable[WebMiddleware]]:
    app = web.Application()
    app["prefix"] = "service"
    app["api_versions"] = (4, 5)
    app.on_startup.append(init)
    app.on_shutdown.append(shutdown)
    app["service.context"] = PrivateContext()
    cors = aiohttp_cors.setup(app, defaults=default_cors_options)
    add_route = app.router.add_route
    root_resource = cors.add(app.router.add_resource(r""))
    cors.add(root_resource.add_route("GET", list_))
    cors.add(root_resource.add_route("POST", create))
    cors.add(root_resource.add_route("DELETE", delete))
    cors.add(add_route("GET", r"/info", get_info))
    cors.add(add_route("POST", r"/start", start))
    cors.add(add_route("POST", r"/stop", stop))
    cors.add(add_route("POST", r"/invoke", invoke))
    return app, []
