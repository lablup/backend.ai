import logging
import re
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, Iterable, Tuple

import aiohttp
import aiohttp_cors
import aiotools
import attrs
import sqlalchemy as sa
import trafaret as t
from aiohttp import web
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.exc import NoResultFound

from ai.backend.common import validators as tx
from ai.backend.common.docker import ImageRef
from ai.backend.common.events import KernelLifecycleEventReason
from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common.types import ClusterMode, SessionTypes, VFolderUsageMode
from ai.backend.manager.registry import check_scaling_group

from ..defs import DEFAULT_IMAGE_ARCH
from ..models import (
    ImageRow,
    UserRow,
    query_accessible_vfolders,
    resolve_group_name_or_id,
    scaling_groups,
    vfolders,
)
from ..models.endpoint import EndpointRow
from ..models.routing import RouteStatus, RoutingRow
from ..types import UserScope
from .auth import auth_required
from .exceptions import (
    InvalidAPIParameters,
    ObjectNotFound,
    ServiceUnavailable,
    VFolderNotFound,
)
from .manager import ALL_ALLOWED, READ_ALLOWED, server_status_required
from .session import query_userinfo
from .types import CORSOptions, WebMiddleware
from .utils import check_api_params, get_access_key_scopes, get_user_uuid_scopes, undefined

if TYPE_CHECKING:
    from .context import RootContext

log = BraceStyleAdapter(logging.getLogger(__name__))


class UndefChecker(t.Trafaret):
    def check_and_return(self, value: Any) -> object:
        if value == undefined:
            return value
        else:
            self._failure("Invalid Undef format", value=value)
            return None


async def is_user_allowed_to_access_resource(
    db_sess: AsyncSession,
    request: web.Request,
    resource_owner: uuid.UUID,
) -> bool:
    if request["user"]["is_superadmin"]:
        return True
    elif request["user"]["is_admin"]:
        query = sa.select(UserRow).filter(UserRow.uuid == resource_owner)
        result = await db_sess.execute(query)
        user = result.scalar()
        return user.domain_name == request["user"]["domain_name"]
    else:
        return request["user"]["uyud"] == resource_owner


@auth_required
@server_status_required(READ_ALLOWED)
@check_api_params(
    t.Dict(
        {
            t.Key("name", default=None): t.Null | t.String,
        }
    )
)
async def list_serve(request: web.Request, params: Any) -> web.Response:
    root_ctx: RootContext = request.app["_root.context"]
    access_key = request["keypair"]["access_key"]

    log.info("SERVE.LIST (email:{}, ak:{})", request["user"]["email"], access_key)
    query_conds = EndpointRow.session_owner == request["user"]["uuid"]
    if params["name"]:
        query_conds &= EndpointRow.name == params["name"]

    async with root_ctx.db.begin_readonly_session() as db_sess:
        query = (
            sa.select(EndpointRow).where(query_conds).options(selectinload(EndpointRow.routings))
        )
        result = await db_sess.execute(query)
        rows = result.scalars().all()

    return web.json_response(
        [
            {
                "id": str(endpoint.id),
                "name": endpoint.name,
                "desired_session_count": endpoint.desired_session_count,
                "active_route_count": len(
                    [r for r in endpoint.routings if r.status == RouteStatus.HEALTHY]
                ),
                "service_endpoint": endpoint.url,
                "is_public": endpoint.open_to_public,
            }
            for endpoint in rows
        ],
        status=200,
    )


@auth_required
@server_status_required(READ_ALLOWED)
async def get_info(request: web.Request) -> web.Response:
    root_ctx: RootContext = request.app["_root.context"]
    access_key = request["keypair"]["access_key"]
    service_id = uuid.UUID(request.match_info["service_id"])

    log.info(
        "SERVE.GET_INFO (email:{}, ak:{}, s:{})", request["user"]["email"], access_key, service_id
    )

    async with root_ctx.db.begin_readonly_session() as db_sess:
        try:
            endpoint = await EndpointRow.get(db_sess, service_id, load_routes=True)
        except NoResultFound:
            raise ObjectNotFound

    await get_user_uuid_scopes(request, {"owner_uuid": endpoint.session_owner})
    resp = {
        "endpoint_id": str(endpoint.id),
        "name": endpoint.name,
        "desired_session_count": endpoint.desired_session_count,
        "active_routes": [
            {
                "route_id": str(r.id),
                "session_id": str(r.session),
                "traffic_ratio": r.traffic_ratio,
            }
            for r in endpoint.routings
            if r.status == RouteStatus.HEALTHY
        ],
        "service_endpoint": endpoint.url,
        "is_public": endpoint.open_to_public,
    }

    return web.json_response(resp, status=200)


@auth_required
@server_status_required(ALL_ALLOWED)
@check_api_params(
    t.Dict(
        {
            tx.AliasedKey(["name", "clientSessionToken"])
            >> "service_name": t.Regexp(r"^(?=.{4,64}$)\w[\w.-]*\w$", re.ASCII),
            tx.AliasedKey(["desired_session_count", "desiredSessionCount"]): t.Int,
            tx.AliasedKey(["image", "lang"]): t.String,
            tx.AliasedKey(["arch", "architecture"], default=DEFAULT_IMAGE_ARCH)
            >> "architecture": t.String,
            tx.AliasedKey(["group", "groupName", "group_name"], default="default"): t.String,
            tx.AliasedKey(["domain", "domainName", "domain_name"], default="default"): t.String,
            tx.AliasedKey(["cluster_size", "clusterSize"], default=1): t.ToInt[1:],  # new in APIv6
            tx.AliasedKey(["cluster_mode", "clusterMode"], default="single-node"): tx.Enum(
                ClusterMode
            ),  # new in APIv6
            t.Key("tag", default=None): t.Null | t.String,
            tx.AliasedKey(["startup_command", "startupCommand"], default=None): t.Null | t.String,
            tx.AliasedKey(["bootstrap_script", "bootstrapScript"], default=None): t.Null | t.String,
            tx.AliasedKey(["callback_url", "callbackUrl", "callbackURL"], default=None): (
                t.Null | tx.URL
            ),
            t.Key("owner_access_key", default=None): t.Null | t.String,
            t.Key("open_to_public", default=False): t.Bool,
            t.Key("config"): t.Dict(
                {
                    t.Key("model"): t.String,
                    tx.AliasedKey(["model_version", "modelVersion"], default=None): (
                        t.Null | t.String
                    ),
                    tx.AliasedKey(
                        ["model_mount_destination", "modelMountDestination"], default="/models"
                    ): t.String,
                    t.Key("environ", default=None): t.Null | t.Mapping(t.String, t.String),
                    # cluster_size is moved to the root-level parameters
                    tx.AliasedKey(["scaling_group", "scalingGroup"], default=None): (
                        t.Null | t.String
                    ),
                    t.Key("resources", default=None): t.Null | t.Mapping(t.String, t.Any),
                    tx.AliasedKey(
                        ["resource_opts", "resourceOpts"], default=None
                    ): t.Null | t.Mapping(t.String, t.Any),
                }
            ),
        }
    ),
)
async def create(request: web.Request, params: Any) -> web.Response:
    root_ctx: RootContext = request.app["_root.context"]
    scopes_param = {
        "owner_access_key": (
            None if params["owner_access_key"] is undefined else params["owner_access_key"]
        ),
    }
    requester_access_key, owner_access_key = await get_access_key_scopes(request, scopes_param)

    async with root_ctx.db.begin_readonly() as conn:
        checked_scaling_group = await check_scaling_group(
            conn,
            params["config"]["scaling_group"],
            SessionTypes.INFERENCE,
            owner_access_key,
            params["domain"],
            params["group"],
        )

        query = (
            sa.select([scaling_groups.c.wsproxy_addr])
            .select_from(scaling_groups)
            .where((scaling_groups.c.name == checked_scaling_group))
        )

        result = await conn.execute(query)
        sgroup = result.first()
        wsproxy_addr = sgroup["wsproxy_addr"]
        if not wsproxy_addr:
            raise ServiceUnavailable("No coordinator configured for this resource group")

        params["config"]["scaling_group"] = checked_scaling_group

        owner_uuid, group_id, resource_policy = await query_userinfo(request, params, conn)
        allowed_vfolder_types = await root_ctx.shared_config.get_vfolder_types()
        try:
            extra_vf_conds = (vfolders.c.id == uuid.UUID(params["config"]["model"])) & (
                vfolders.c.usage_mode == VFolderUsageMode.MODEL
            )
            matched_vfolders = await query_accessible_vfolders(
                conn,
                owner_uuid,
                user_role=request["user"]["role"],
                domain_name=params["domain"],
                allowed_vfolder_types=allowed_vfolder_types,
                extra_vf_conds=extra_vf_conds,
            )
        except Exception as e:
            # just catching ValueError | VFolderNotFound will raise
            # TypeError: catching classes that do not inherit from BaseException is not allowed
            if isinstance(e, ValueError) or isinstance(e, VFolderNotFound):
                try:
                    extra_vf_conds = (vfolders.c.name == params["config"]["model"]) & (
                        vfolders.c.usage_mode == VFolderUsageMode.MODEL
                    )
                    matched_vfolders = await query_accessible_vfolders(
                        conn,
                        owner_uuid,
                        user_role=request["user"]["role"],
                        domain_name=params["domain"],
                        allowed_vfolder_types=allowed_vfolder_types,
                        extra_vf_conds=extra_vf_conds,
                    )
                except VFolderNotFound as e:
                    raise VFolderNotFound("Cannot find model folder") from e
            else:
                raise
        model_id = matched_vfolders[0]["id"]

    async with root_ctx.db.begin_readonly_session() as session:
        image_row = await ImageRow.resolve(
            session,
            [
                ImageRef(params["image"], ["*"], params["architecture"]),
                params["image"],
            ],
        )

    params["config"]["mount_map"] = {model_id: params["config"]["model_mount_destination"]}

    # check if session is valid to be created
    await root_ctx.registry.create_session(
        "",
        params["image"],
        params["architecture"],
        UserScope(
            domain_name=params["domain"],
            group_id=group_id,
            user_uuid=request["user"]["uuid"],
            user_role=request["user"]["role"],
        ),
        owner_access_key,
        resource_policy,
        SessionTypes.INFERENCE,
        params["config"],
        params["cluster_mode"],
        params["cluster_size"],
        dry_run=True,  # Setting this to True will prevent actual session from being enqueued
        bootstrap_script=params["bootstrap_script"],
        startup_command=params["startup_command"],
        tag=params["tag"],
        callback_url=params["callback_url"],
    )

    async with root_ctx.db.begin_session() as db_sess:
        project_id = await resolve_group_name_or_id(
            await db_sess.connection(), params["domain"], params["group"]
        )
        if project_id is None:
            raise InvalidAPIParameters(f"Invalid group name {project_id}")
        endpoint = EndpointRow(
            params["service_name"],
            request["user"]["uuid"],
            owner_uuid,
            params["desired_session_count"],
            image_row,
            model_id,
            params["domain"],
            project_id,
            checked_scaling_group,
            params["config"]["resources"],
            params["cluster_mode"],
            params["cluster_size"],
            model_mount_destination=params["config"]["model_mount_destination"],
            tag=params["tag"],
            startup_command=params["startup_command"],
            callback_url=params["callback_url"],
            environ=params["config"]["environ"],
            bootstrap_script=params["bootstrap_script"],
            resource_opts=params["config"]["resource_opts"],
            open_to_public=params["open_to_public"],
        )
        db_sess.add(endpoint)
        await db_sess.commit()

    return web.json_response({"endpoint_id": str(endpoint.id)})


@auth_required
@server_status_required(READ_ALLOWED)
async def delete(request: web.Request) -> web.Response:
    root_ctx: RootContext = request.app["_root.context"]
    access_key = request["keypair"]["access_key"]
    service_id = uuid.UUID(request.match_info["service_id"])

    log.info(
        "SERVE.DELETE (email:{}, ak:{}, s:{})", request["user"]["email"], access_key, service_id
    )

    async with root_ctx.db.begin_readonly_session() as db_sess:
        try:
            endpoint = await EndpointRow.get(db_sess, service_id, load_routes=True)
        except NoResultFound:
            raise ObjectNotFound
    await get_user_uuid_scopes(request, {"owner_uuid": endpoint.session_owner})

    async with root_ctx.db.begin_session() as db_sess:
        query = (
            sa.update(EndpointRow)
            .where(EndpointRow.id == service_id)
            .values({"desired_session_count": -1})
        )
        await db_sess.execute(query)
    return web.json_response({"success": True}, status=200)


@auth_required
@server_status_required(READ_ALLOWED)
async def sync(request: web.Request) -> web.Response:
    root_ctx: RootContext = request.app["_root.context"]
    access_key = request["keypair"]["access_key"]
    service_id = uuid.UUID(request.match_info["service_id"])

    log.info("SERVE.SYNC (email:{}, ak:{}, s:{})", request["user"]["email"], access_key, service_id)

    async with root_ctx.db.begin_readonly_session() as db_sess:
        try:
            endpoint = await EndpointRow.get(db_sess, service_id, load_routes=True)
        except NoResultFound:
            raise ObjectNotFound
    await get_user_uuid_scopes(request, {"owner_uuid": endpoint.session_owner})

    async with root_ctx.db.begin_session() as db_sess:
        await root_ctx.registry.update_appproxy_endpoint_routes(db_sess, endpoint)
    return web.json_response({"success": True}, status=200)


@auth_required
@server_status_required(READ_ALLOWED)
@check_api_params(
    t.Dict(
        {
            t.Key("to"): t.Int,
        }
    ),
)
async def scale(request: web.Request, params: Any) -> web.Response:
    root_ctx: RootContext = request.app["_root.context"]
    access_key = request["keypair"]["access_key"]
    service_id = uuid.UUID(request.match_info["service_id"])

    log.info(
        "SERVE.SCALE (email:{}, ak:{}, s:{})", request["user"]["email"], access_key, service_id
    )

    async with root_ctx.db.begin_readonly_session() as db_sess:
        try:
            endpoint = await EndpointRow.get(db_sess, service_id, load_routes=True)
        except NoResultFound:
            raise ObjectNotFound
    await get_user_uuid_scopes(request, {"owner_uuid": endpoint.session_owner})

    if params["to"] < 0:
        raise InvalidAPIParameters("Amount of desired session count cannot be a negative number")
    if params["to"] == len(endpoint.routings):
        return web.json_response(
            {"current_route_count": len(endpoint.routings), "target_count": params["to"]}
        )

    async with root_ctx.db.begin_session() as db_sess:
        query = (
            sa.update(EndpointRow)
            .where(EndpointRow.id == service_id)
            .values({"desired_session_count": params["to"]})
        )
        await db_sess.execute(query)
        return web.json_response(
            {"current_route_count": len(endpoint.routings), "target_count": params["to"]}
        )


@auth_required
@server_status_required(READ_ALLOWED)
@check_api_params(
    t.Dict(
        {
            t.Key("traffic_ratio"): t.Float[0:],
        }
    ),
)
async def update_route(request: web.Request, params: Any) -> web.Response:
    root_ctx: RootContext = request.app["_root.context"]
    access_key = request["keypair"]["access_key"]
    service_id = uuid.UUID(request.match_info["service_id"])
    route_id = uuid.UUID(request.match_info["route_id"])

    log.info(
        "SERVE.UPDATE_ROUTE (email:{}, ak:{}, s:{}, r:{})",
        request["user"]["email"],
        access_key,
        service_id,
        route_id,
    )

    async with root_ctx.db.begin_session() as db_sess:
        try:
            route = await RoutingRow.get(db_sess, route_id, load_endpoint=True)
        except NoResultFound:
            raise ObjectNotFound
        if route.endpoint != service_id:
            raise ObjectNotFound
        await get_user_uuid_scopes(request, {"owner_uuid": route.endpoint_row.session_owner})

        query = (
            sa.update(RoutingRow)
            .where(RoutingRow.id == route_id)
            .values({"traffic_ratio": params["traffic_ratio"]})
        )
        await db_sess.execute(query)
        endpoint = await EndpointRow.get(db_sess, service_id, load_routes=True)
        try:
            await root_ctx.registry.update_appproxy_endpoint_routes(db_sess, endpoint)
        except aiohttp.ClientError as e:
            log.warn("failed to communicate with AppProxy endpoint: {}", str(e))
        return web.json_response({"success": True})


@auth_required
@server_status_required(READ_ALLOWED)
async def delete_route(request: web.Request) -> web.Response:
    root_ctx: RootContext = request.app["_root.context"]
    access_key = request["keypair"]["access_key"]
    service_id = uuid.UUID(request.match_info["service_id"])
    route_id = uuid.UUID(request.match_info["route_id"])

    log.info(
        "SERVE.DELETE_ROUTE (email:{}, ak:{}, s:{})",
        request["user"]["email"],
        access_key,
        service_id,
    )
    async with root_ctx.db.begin_readonly_session() as db_sess:
        try:
            route = await RoutingRow.get(db_sess, route_id, load_session=True)
        except NoResultFound:
            raise ObjectNotFound
        if route.endpoint != service_id:
            raise ObjectNotFound
    await get_user_uuid_scopes(request, {"owner_uuid": route.endpoint_row.session_owner})
    if route.status == RouteStatus.PROVISIONING:
        raise InvalidAPIParameters("Cannot remove route in PROVISIONING status")

    await root_ctx.registry.destroy_session(
        route.session_row,
        forced=False,
        reason=KernelLifecycleEventReason.SERVICE_SCALED_DOWN,
    )

    async with root_ctx.db.begin_session() as db_sess:
        query = (
            sa.update(EndpointRow)
            .where(EndpointRow.id == service_id)
            .values({"desired_session_count": route.endpoint_row.desired_session_count})
        )
        await db_sess.execute(query)
        return web.json_response({"success": True})


@auth_required
@server_status_required(READ_ALLOWED)
@check_api_params(
    t.Dict(
        {
            t.Key("duration"): tx.TimeDuration,
        }
    ),
)
async def generate_token(request: web.Request, params: Any) -> web.Response:
    root_ctx: RootContext = request.app["_root.context"]
    access_key = request["keypair"]["access_key"]
    service_id = uuid.UUID(request.match_info["service_id"])

    log.info(
        "SERVE.GENERATE_TOKEN (email:{}, ak:{}, s:{})",
        request["user"]["email"],
        access_key,
        service_id,
    )

    async with root_ctx.db.begin_readonly_session() as db_sess:
        try:
            endpoint = await EndpointRow.get(db_sess, service_id, load_routes=True)
        except NoResultFound:
            raise ObjectNotFound
        query = (
            sa.select([scaling_groups.c.wsproxy_addr, scaling_groups.c.wsproxy_api_token])
            .select_from(scaling_groups)
            .where((scaling_groups.c.name == endpoint.resource_group))
        )

        result = await db_sess.execute(query)
        sgroup = result.first()
        wsproxy_addr = sgroup["wsproxy_addr"]
        wsproxy_api_token = sgroup["wsproxy_api_token"]

    await get_user_uuid_scopes(request, {"owner_uuid": endpoint.session_owner})

    exp = datetime.now() + params["duration"]
    body = {"user_uuid": str(endpoint.session_owner), "exp": int(exp.timestamp())}
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{wsproxy_addr}/v2/endpoints/{endpoint.id}/token",
            json=body,
            headers={
                "X-BackendAI-Token": wsproxy_api_token,
            },
        ) as resp:
            token_json = await resp.json()
            return web.json_response({"token": token_json["token"]})


@attrs.define(slots=True, auto_attribs=True, init=False)
class PrivateContext:
    database_ptask_group: aiotools.PersistentTaskGroup


async def init(app: web.Application) -> None:
    app_ctx: PrivateContext = app["services.context"]
    app_ctx.database_ptask_group = aiotools.PersistentTaskGroup()


async def shutdown(app: web.Application) -> None:
    app_ctx: PrivateContext = app["services.context"]
    await app_ctx.database_ptask_group.shutdown()


def create_app(
    default_cors_options: CORSOptions,
) -> Tuple[web.Application, Iterable[WebMiddleware]]:
    app = web.Application()
    app["prefix"] = "services"
    app["api_versions"] = (4, 5)
    app.on_startup.append(init)
    app.on_shutdown.append(shutdown)
    app["services.context"] = PrivateContext()
    cors = aiohttp_cors.setup(app, defaults=default_cors_options)
    add_route = app.router.add_route
    root_resource = cors.add(app.router.add_resource(r""))
    cors.add(root_resource.add_route("GET", list_serve))
    cors.add(root_resource.add_route("POST", create))
    cors.add(add_route("GET", "/{service_id}", get_info))
    cors.add(add_route("DELETE", "/{service_id}", delete))
    cors.add(add_route("POST", "/{service_id}/scale", scale))
    cors.add(add_route("POST", "/{service_id}/sync", sync))
    cors.add(add_route("PUT", "/{service_id}/routings/{route_id}", update_route))
    cors.add(add_route("DELETE", "/{service_id}/routings/{route_id}", delete_route))
    cors.add(add_route("POST", "/{service_id}/token", generate_token))
    return app, []
