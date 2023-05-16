import functools
import logging
from typing import Any, Awaitable, Callable, Iterable, Mapping, Tuple

import aiohttp
import aiohttp_cors
import sqlalchemy as sa
import trafaret as t
from aiohttp import web

from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.manager.models.storage import AUTH_TOKEN_HDR

from ..exceptions import InvalidArgument
from ..models import (
    VFolderAccessStatus,
    VFolderPermission,
    query_accessible_vfolders,
    vfolder_permissions,
    vfolders,
)
from .auth import auth_required
from .context import RootContext
from .exceptions import InvalidAPIParameters, VFolderNotFound
from .manager import READ_ALLOWED, server_status_required
from .types import CORSOptions, WebMiddleware
from .utils import check_api_params
from .vfolder import ensure_vfolder_status

logger = logging.getLogger(__name__)

log = BraceStyleAdapter(logging.getLogger(__name__))

VFolderRow = Mapping[str, Any]


async def get_vfid(root_ctx: RootContext, host: str, name: str) -> str:
    async with root_ctx.db.begin_readonly() as conn:
        query = (
            sa.select([vfolders.c.id])
            .select_from(vfolders)
            .where((vfolders.c.host == host) & (vfolders.c.name == name))
        )
        folder_id = await conn.scalar(query)
        return folder_id


def vfolder_permission_required(perm: VFolderPermission):
    """
    Checks if the target vfolder exists and is either:
    - owned by the current access key, or
    - allowed accesses by the access key under the specified permission.

    The decorated handler should accept an extra argument
    which contains a dict object describing the matched VirtualFolder table row.
    """

    def _wrapper(handler: Callable[..., Awaitable[web.Response]]):
        @functools.wraps(handler)
        async def _wrapped(request: web.Request, *args, **kwargs) -> web.Response:
            root_ctx: RootContext = request.app["_root.context"]
            domain_name = request["user"]["domain_name"]
            user_role = request["user"]["role"]
            user_uuid = request["user"]["uuid"]

            params = await request.json()
            folder_names = params["vfolders"]

            for folder_name in folder_names:
                allowed_vfolder_types = await root_ctx.shared_config.get_vfolder_types()
                vf_user_cond = None
                vf_group_cond = None
                if perm == VFolderPermission.READ_ONLY:
                    # if READ_ONLY is requested, any permission accepts.
                    invited_perm_cond = vfolder_permissions.c.permission.in_(
                        [
                            VFolderPermission.READ_ONLY,
                            VFolderPermission.READ_WRITE,
                            VFolderPermission.RW_DELETE,
                        ]
                    )
                    if not request["is_admin"]:
                        vf_group_cond = vfolders.c.permission.in_(
                            [
                                VFolderPermission.READ_ONLY,
                                VFolderPermission.READ_WRITE,
                                VFolderPermission.RW_DELETE,
                            ]
                        )
                elif perm == VFolderPermission.READ_WRITE:
                    invited_perm_cond = vfolder_permissions.c.permission.in_(
                        [
                            VFolderPermission.READ_WRITE,
                            VFolderPermission.RW_DELETE,
                        ]
                    )
                    if not request["is_admin"]:
                        vf_group_cond = vfolders.c.permission.in_(
                            [
                                VFolderPermission.READ_WRITE,
                                VFolderPermission.RW_DELETE,
                            ]
                        )
                elif perm == VFolderPermission.RW_DELETE:
                    # If RW_DELETE is requested, only RW_DELETE accepts.
                    invited_perm_cond = (
                        vfolder_permissions.c.permission == VFolderPermission.RW_DELETE
                    )
                    if not request["is_admin"]:
                        vf_group_cond = vfolders.c.permission == VFolderPermission.RW_DELETE
                else:
                    # Otherwise, just compare it as-is (for future compatibility).
                    invited_perm_cond = vfolder_permissions.c.permission == perm
                    if not request["is_admin"]:
                        vf_group_cond = vfolders.c.permission == perm
                async with root_ctx.db.begin() as conn:
                    entries = await query_accessible_vfolders(
                        conn,
                        user_uuid,
                        user_role=user_role,
                        domain_name=domain_name,
                        allowed_vfolder_types=allowed_vfolder_types,
                        extra_vf_conds=(vfolders.c.name == folder_name),
                        extra_invited_vf_conds=invited_perm_cond,
                        extra_vf_user_conds=vf_user_cond,
                        extra_vf_group_conds=vf_group_cond,
                    )
                    if len(entries) == 0:
                        raise VFolderNotFound("Your operation may be permission denied.")
            return await handler(request, *args, **kwargs)

        return _wrapped

    return _wrapper


def vfolder_check_exists():
    def _wrapper(handler: Callable[..., Awaitable[web.Response]]):
        @functools.wraps(handler)
        async def _wrapped(request: web.Request, *args, **kwargs) -> web.Response:
            root_ctx: RootContext = request.app["_root.context"]
            user_uuid = request["user"]["uuid"]

            params = await request.json()
            folder_names = params["vfolders"]

            for folder_name in folder_names:
                async with root_ctx.db.begin() as conn:
                    j = sa.join(
                        vfolders,
                        vfolder_permissions,
                        vfolders.c.id == vfolder_permissions.c.vfolder,
                        isouter=True,
                    )
                    query = (
                        sa.select("*")
                        .select_from(j)
                        .where(
                            (
                                (vfolders.c.user == user_uuid)
                                | (vfolder_permissions.c.user == user_uuid)
                            )
                            & (vfolders.c.name == folder_name)
                        )
                    )
                    try:
                        result = await conn.execute(query)
                        row = result.first()
                    except sa.exc.DataError:
                        raise InvalidAPIParameters
                    if row is None:
                        raise VFolderNotFound(folder_name)
            return await handler(request, *args, **kwargs)

        return _wrapped

    return _wrapper


@auth_required
@server_status_required(READ_ALLOWED)
@check_api_params(
    t.Dict(
        {
            t.Key("host"): t.String,
            t.Key("vfolders"): t.List(t.String),
        },
    ),
)
@vfolder_permission_required(VFolderPermission.READ_WRITE)
@vfolder_check_exists()
async def create_or_update_filebrowser(
    request: web.Request,
    params: Any,
) -> web.Response:
    root_ctx: RootContext = request.app["_root.context"]
    vfolders = []
    host = params["host"]
    for vfolder_name in params["vfolders"]:
        vfid = (await get_vfid(root_ctx, host, vfolder_name),)
        vfolders.append(
            {
                "name": vfolder_name,
                "vfid": str(vfid[0]),
            },
        )
        await ensure_vfolder_status(request, VFolderAccessStatus.READABLE, folder_id=str(vfid[0]))

    proxy_name, tmp = root_ctx.storage_manager.split_host(host)
    try:
        proxy_info = root_ctx.storage_manager._proxies[proxy_name]
    except KeyError:
        raise InvalidArgument("There is no such storage proxy", proxy_name)
    headers = {}

    headers[AUTH_TOKEN_HDR] = proxy_info.secret
    try:
        async with proxy_info.session.request(
            "POST",
            proxy_info.manager_api_url / "storage/filebrowser/create",
            headers=headers,
            json={"host": host, "vfolders": vfolders},
        ) as client_resp:
            return web.json_response(await client_resp.json())
    except aiohttp.ClientResponseError:
        raise


@auth_required
@server_status_required(READ_ALLOWED)
@check_api_params(
    t.Dict(
        {
            t.Key("container_id"): t.String,
        },
    ),
)
async def destroy_filebrowser(
    request: web.Request,
    params: Any,
) -> web.Response:
    root_ctx: RootContext = request.app["_root.context"]
    container_id = params["container_id"]

    volumes = await root_ctx.storage_manager.get_all_volumes()

    # search for volume among available volumes which has file browser container id in order to destroy
    for volume in volumes:
        proxy_name = volume[0]
        try:
            proxy_info = root_ctx.storage_manager._proxies[proxy_name]
        except KeyError:
            raise InvalidArgument("There is no such storage proxy", proxy_name)

        headers = {}
        headers[AUTH_TOKEN_HDR] = proxy_info.secret
        auth_token = proxy_info.secret
        try:
            async with proxy_info.session.request(
                "DELETE",
                proxy_info.manager_api_url / "storage/filebrowser/destroy",
                headers=headers,
                json={"container_id": container_id, "auth_token": auth_token},
            ) as client_resp:
                return web.json_response(await client_resp.json())
        except aiohttp.ClientResponseError:
            raise
    return web.json_response({"status": "fail"})


async def init(app: web.Application) -> None:
    pass


async def shutdown(app: web.Application) -> None:
    pass


def create_app(
    default_cors_options: CORSOptions,
) -> Tuple[web.Application, Iterable[WebMiddleware]]:
    app = web.Application()
    app["prefix"] = "storage/filebrowser"
    app["api_versions"] = (
        2,
        3,
        4,
    )
    app.on_startup.append(init)
    app.on_shutdown.append(shutdown)
    cors = aiohttp_cors.setup(app, defaults=default_cors_options)
    cors.add(app.router.add_route("POST", "/create", create_or_update_filebrowser))
    cors.add(app.router.add_route("DELETE", "/destroy", destroy_filebrowser))

    return app, []
