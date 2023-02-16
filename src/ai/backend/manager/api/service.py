import asyncio
import logging
import secrets
from datetime import datetime
from typing import TYPE_CHECKING, Any, Iterable, MutableMapping, Tuple, Union

import aiohttp_cors
import aiotools
import attrs
import sqlalchemy as sa
import trafaret as t
from aiohttp import web
from dateutil.parser import isoparse
from dateutil.tz import tzutc

from ai.backend.common import validators as tx
from ai.backend.common.docker import ImageRef
from ai.backend.common.exception import AliasResolutionFailed, UnknownImageReference
from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common.types import ClusterMode, SessionTypes
from ai.backend.common.utils import str_to_timedelta

from ..defs import DEFAULT_ROLE
from ..models import ImageRow, domains, query_bootstrap_script, verify_vfolder_name, vfolders
from ..models.endpoint import EndpointRow
from ..models.routing import RoutingRow
from ..models.session import SessionRow, SessionStatus
from ..types import UserScope
from .auth import auth_required
from .exceptions import (
    BackendError,
    ImageNotFound,
    InternalServerError,
    InvalidAPIParameters,
    UnknownImageReferenceError,
)
from .manager import ALL_ALLOWED, READ_ALLOWED, server_status_required
from .session import query_userinfo
from .types import CORSOptions, WebMiddleware
from .utils import check_api_params

if TYPE_CHECKING:
    from .context import RootContext

log = BraceStyleAdapter(logging.getLogger(__name__))


@auth_required
@server_status_required(READ_ALLOWED)
@check_api_params(
    t.Dict(
        {
            tx.AliasedKey(["project_id", "projectId"]): tx.UUID,
        }
    ),
)
async def list_serve(request: web.Request, params: Any) -> web.Response:
    root_ctx: RootContext = request.app["_root.context"]
    access_key = request["keypair"]["access_key"]
    project_id = params["project_id"]

    log.info("SERVE.LIST (email:{}, ak:{})", request["user"]["email"], access_key)

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

    log.info("SERVE.GET_INFO (email:{}, ak:{})", request["user"]["email"], access_key)

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
            tx.AliasedKey(["serving_name", "servingName"]): t.String,
            tx.AliasedKey(["model_id", "modelId"]): tx.UUID,
            tx.AliasedKey(["model_version", "modelVersion"]): t.String,
            tx.AliasedKey(["image_ref", "imageRef"]): t.String,
            tx.AliasedKey(
                ["group", "group_name", "groupName", "project_name", "projectName"], default=None
            ): tx.UUID
            | t.String
            | t.Null,
            tx.AliasedKey(["resource_opts", "resourceOpts"], default=dict): t.Mapping(
                t.String, t.Any
            ),
            tx.AliasedKey(["cluster_size", "clusterSize"], default=1): t.ToInt[1:],
            tx.AliasedKey(["cluster_mode", "clusterMode"], default="single-node"): tx.Enum(
                ClusterMode
            ),
            t.Key("tag", default=None): t.Null | t.String,
            t.Key("config", default=dict): t.Mapping(t.String, t.Any),
        }
    ),
)
async def create(request: web.Request, params: Any) -> web.Response:
    root_ctx: RootContext = request.app["_root.context"]
    app_ctx: PrivateContext = request.app["session.context"]
    access_key = request["keypair"]["access_key"]
    domain_name = request["user"]["domain_name"]
    user_role = request["user"]["role"]

    log.info("SERVE.CREATE (email:{}, ak:{})", request["user"]["email"], access_key)
    resp: MutableMapping[str, Any] = {}

    # Resolve the image reference.
    try:
        async with root_ctx.db.begin_readonly_session() as session:
            image_row = await ImageRow.resolve(
                session,
                [
                    ImageRef(params["image"], ["*"], params["architecture"]),
                    params["image"],
                ],
            )
        requested_image_ref = image_row.image_ref
        model_mount_path = image_row.labels.get("ai.backend.model-path")
        async with root_ctx.db.begin_readonly() as conn:
            query = (
                sa.select([domains.c.allowed_docker_registries])
                .select_from(domains)
                .where(domains.c.name == params["domain"])
            )
            allowed_registries = await conn.scalar(query)
            if requested_image_ref.registry not in allowed_registries:
                raise AliasResolutionFailed
    except AliasResolutionFailed:
        raise ImageNotFound("unknown alias or disallowed registry")

    # Check work directory and reserved name directory.
    mount_map = params["config"].get("mount_map")
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
                    "Alias name cannot be set to an existing folder name: " + str(alias_name)
                )

    # Append model mount path
    mounts: list[str] = params["config"].get("mounts")
    async with root_ctx.db.begin_readonly() as db_conn:
        query = sa.select([vfolders.c.name]).where(vfolders.c.id == params["model_id"])
        result = await db_conn.execute(query)
        vfolder_name = result.first()["name"]
    model_path = f"{vfolder_name}/versions/{params['model_version']}"
    mounts = [*mounts, model_path]
    mount_map = {
        **mount_map,
        model_path: model_mount_path,
    }
    params["config"]["mounts"] = mounts
    params["config"]["mount_map"] = mount_map
    for kern_config in params["config"]["kernel_configs"]:
        kern_config["mounts"] = mounts
        kern_config["mount_map"] = mount_map

    # # Check existing (owner_access_key, session_name) instance
    # try:
    #     # NOTE: We can reuse the session IDs of TERMINATED sessions only.
    #     # NOTE: Reusing a session in the PENDING status returns an empty value in service_ports.
    #     async with root_ctx.db.begin_readonly_session() as db_sess:
    #         sess = await SessionRow.get_session_with_main_kernel(
    #             params["session_name"],
    #             access_key,
    #             db_session=db_sess,
    #         )
    #     running_image_ref = ImageRef(
    #         sess.main_kernel.image, [sess.main_kernel.registry], sess.main_kernel.architecture
    #     )
    #     if running_image_ref != requested_image_ref:
    #         # The image must be same if get_or_create() called multiple times
    #         # against an existing (non-terminated) session
    #         raise SessionAlreadyExists(extra_data={"existingSessionId": str(sess.id)})
    #     if not params["reuse"]:
    #         # Respond as error since the client did not request to reuse,
    #         # but provide the overlapping session ID for later use.
    #         raise SessionAlreadyExists(extra_data={"existingSessionId": str(sess.id)})
    #     # Respond as success with the reused session's information.
    #     return web.json_response(
    #         {
    #             "sessionId": str(sess.id),
    #             "sessionName": str(sess.name),
    #             "status": sess.status.name,
    #             "service_ports": sess.main_kernel.service_ports,
    #             "created": False,
    #         },
    #         status=200,
    #     )
    # except SessionNotFound:
    #     # It's time to create a new session.
    #     pass

    # if params["session_type"] == SessionTypes.BATCH and not params["startup_command"]:
    #     raise InvalidAPIParameters("Batch sessions must have a non-empty startup command.")
    # if params["session_type"] != SessionTypes.BATCH and params["starts_at"]:
    #     raise InvalidAPIParameters("Parameter starts_at should be used only for batch sessions")

    starts_at: Union[datetime, None] = None
    if params["starts_at"]:
        try:
            starts_at = isoparse(params["starts_at"])
        except ValueError:
            _td = str_to_timedelta(params["starts_at"])
            starts_at = datetime.now(tzutc()) + _td

    # if params["cluster_size"] > 1:
    #     log.debug(" -> cluster_mode:{} (replicate)", params["cluster_mode"])

    # if params["dependencies"] is None:
    #     params["dependencies"] = []

    session_creation_id = secrets.token_urlsafe(16)

    async with root_ctx.db.begin_readonly() as conn:
        owner_uuid, group_id, resource_policy = await query_userinfo(request, params, conn)

        # Use keypair bootstrap_script if it is not delivered as a parameter
        if not params["bootstrap_script"]:
            script, _ = await query_bootstrap_script(conn, access_key)
            params["bootstrap_script"] = script

    try:
        session_id = await asyncio.shield(
            app_ctx.database_ptask_group.create_task(
                root_ctx.registry.enqueue_session(
                    session_creation_id,
                    params["serving_name"],
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
                    SessionTypes.INTERACTIVE,
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
        resp["sessionId"] = str(session_id)  # changed since API v5
        resp["sessionName"] = str(params["serving_name"])
        resp["status"] = SessionStatus.PENDING.name
        resp["servicePorts"] = []
        resp["created"] = True

        # if not params["enqueue_only"]:
        #     app_ctx.pending_waits.add(current_task)
        #     max_wait = params["max_wait_seconds"]
        #     try:
        #         if max_wait > 0:
        #             with timeout(max_wait):
        #                 await start_event.wait()
        #         else:
        #             await start_event.wait()
        #     except asyncio.TimeoutError:
        #         resp["status"] = "TIMEOUT"
        #     else:
        #         await asyncio.sleep(0.5)
        #         async with root_ctx.db.begin_readonly_session() as db_sess:
        #             query = sa.select(KernelRow.status, KernelRow.service_ports).where(
        #                 (KernelRow.session_id == session_id)
        #                 & (KernelRow.cluster_role == DEFAULT_ROLE)
        #             )
        #             result = await db_sess.execute(query)
        #             row = result.first()
        #         if row.status == KernelStatus.RUNNING:
        #             resp["status"] = "RUNNING"
        #             for item in row.service_ports:
        #                 response_dict = {
        #                     "name": item["name"],
        #                     "protocol": item["protocol"],
        #                     "ports": item["container_ports"],
        #                 }
        #                 if "url_template" in item.keys():
        #                     response_dict["url_template"] = item["url_template"]
        #                 if "allowed_arguments" in item.keys():
        #                     response_dict["allowed_arguments"] = item["allowed_arguments"]
        #                 if "allowed_envs" in item.keys():
        #                     response_dict["allowed_envs"] = item["allowed_envs"]
        #                 resp["servicePorts"].append(response_dict)
        #         else:
        #             resp["status"] = row.status.name
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
    return web.json_response(resp, status=201)


@auth_required
@server_status_required(READ_ALLOWED)
@check_api_params(
    t.Dict(
        {
            tx.AliasedKey(["endpoint_id", "endpointId"]): tx.UUID | t.String,
        }
    ),
)
async def start(request: web.Request, params: Any) -> web.Response:
    access_key = request["keypair"]["access_key"]

    log.info("SERVE.START (email:{}, ak:{})", request["user"]["email"], access_key)
    return web.Response(status=204)


@auth_required
@server_status_required(READ_ALLOWED)
@check_api_params(
    t.Dict(
        {
            tx.AliasedKey(["endpoint_id", "endpointId"]): tx.UUID | t.String,
        }
    ),
)
async def stop(request: web.Request, params: Any) -> web.Response:
    access_key = request["keypair"]["access_key"]

    log.info("SERVE.STOP (email:{}, ak:{})", request["user"]["email"], access_key)
    return web.Response(status=204)


@auth_required
@server_status_required(READ_ALLOWED)
@check_api_params(
    t.Dict(
        {
            tx.AliasedKey(["endpoint_id", "endpointId"]): tx.UUID | t.String,
            tx.AliasedKey(["input_args", "inputArgs"], default=dict): t.Mapping(t.String, t.Any),
        }
    ),
)
async def invoke_serving(request: web.Request, params: Any) -> web.Response:
    access_key = request["keypair"]["access_key"]

    log.info("SERVE.INVOKE (email:{}, ak:{})", request["user"]["email"], access_key)
    return web.Response(status=204)


@auth_required
@server_status_required(READ_ALLOWED)
@check_api_params(
    t.Dict(
        {
            tx.AliasedKey(["endpoint_id", "endpointId"]): tx.UUID | t.String,
        }
    ),
)
async def delete(request: web.Request, params: Any) -> web.Response:
    access_key = request["keypair"]["access_key"]

    log.info("SERVE.DELETE (email:{}, ak:{})", request["user"]["email"], access_key)
    return web.Response(status=204)


@attrs.define(slots=True, auto_attribs=True, init=False)
class PrivateContext:
    database_ptask_group: aiotools.PersistentTaskGroup


async def init(app: web.Application) -> None:
    app_ctx: PrivateContext = app["service.context"]
    app_ctx.database_ptask_group = aiotools.PersistentTaskGroup()


async def shutdown(app: web.Application) -> None:
    app_ctx: PrivateContext = app["service.context"]
    await app_ctx.database_ptask_group.shutdown()


def create_app(
    default_cors_options: CORSOptions,
) -> Tuple[web.Application, Iterable[WebMiddleware]]:
    app = web.Application()
    app["api_versions"] = (4, 5)
    app.on_startup.append(init)
    app.on_shutdown.append(shutdown)
    app["service.context"] = PrivateContext()
    cors = aiohttp_cors.setup(app, defaults=default_cors_options)
    add_route = app.router.add_route
    root_resource = cors.add(app.router.add_resource(r""))
    cors.add(root_resource.add_route("GET", list_serve))
    cors.add(root_resource.add_route("POST", create))
    cors.add(root_resource.add_route("DELETE", delete))
    cors.add(add_route("GET", r"/_/info", get_info))
    cors.add(add_route("POST", r"/_/start", start))
    cors.add(add_route("POST", r"/_/stop", stop))
    cors.add(add_route("POST", r"/_/invoke", invoke_serving))
    return app, []
