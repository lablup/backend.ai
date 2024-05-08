import logging
import re
from typing import TYPE_CHECKING, Any, Tuple

import aiohttp_cors
import trafaret as t
from aiohttp import web

from ai.backend.common import msgpack
from ai.backend.common.logging import BraceStyleAdapter

from ..models import (
    MAXIMUM_DOTFILE_SIZE,
    keypairs,
    query_accessible_vfolders,
    query_bootstrap_script,
    query_owned_dotfiles,
    verify_dotfile_name,
    vfolders,
)
from .auth import auth_required
from .exceptions import (
    DotfileAlreadyExists,
    DotfileCreationFailed,
    DotfileNotFound,
    InvalidAPIParameters,
)
from .manager import READ_ALLOWED, server_status_required
from .types import CORSOptions, Iterable, WebMiddleware
from .utils import check_api_params, get_access_key_scopes

if TYPE_CHECKING:
    from .context import RootContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


@server_status_required(READ_ALLOWED)
@auth_required
@check_api_params(
    t.Dict(
        {
            t.Key("data"): t.String(max_length=MAXIMUM_DOTFILE_SIZE),
            t.Key("path"): t.String,
            t.Key("permission"): t.Regexp(r"^[0-7]{3}$", re.ASCII),
            t.Key("owner_access_key", default=None): t.Null | t.String,
        },
    )
)
async def create(request: web.Request, params: Any) -> web.Response:
    requester_access_key, owner_access_key = await get_access_key_scopes(request, params)
    log.info(
        "USERCONFIG.CREATE (ak:{0}/{1})",
        requester_access_key,
        owner_access_key if owner_access_key != requester_access_key else "*",
    )
    root_ctx: RootContext = request.app["_root.context"]
    user_uuid = request["user"]["uuid"]
    async with root_ctx.db.begin() as conn:
        path: str = params["path"]
        dotfiles, leftover_space = await query_owned_dotfiles(conn, owner_access_key)
        if leftover_space == 0:
            raise DotfileCreationFailed("No leftover space for dotfile storage")
        if len(dotfiles) == 100:
            raise DotfileCreationFailed("Dotfile creation limit reached")
        if not verify_dotfile_name(path):
            raise InvalidAPIParameters("dotfile path is reserved for internal operations.")
        duplicate_vfolder = await query_accessible_vfolders(
            conn, user_uuid, extra_vf_conds=(vfolders.c.name == path)
        )
        if len(duplicate_vfolder) > 0:
            raise InvalidAPIParameters("dotfile path conflicts with your dot-prefixed vFolder")
        duplicate = [x for x in dotfiles if x["path"] == path]
        if len(duplicate) > 0:
            raise DotfileAlreadyExists
        new_dotfiles = list(dotfiles)
        new_dotfiles.append({"path": path, "perm": params["permission"], "data": params["data"]})
        dotfile_packed = msgpack.packb(new_dotfiles)
        if len(dotfile_packed) > MAXIMUM_DOTFILE_SIZE:
            raise DotfileCreationFailed("No leftover space for dotfile storage")

        query = (
            keypairs.update()
            .values(dotfiles=dotfile_packed)
            .where(keypairs.c.access_key == owner_access_key)
        )
        await conn.execute(query)
    return web.json_response({})


@auth_required
@server_status_required(READ_ALLOWED)
@check_api_params(
    t.Dict({
        t.Key("path", default=None): t.Null | t.String,
        t.Key("owner_access_key", default=None): t.Null | t.String,
    })
)
async def list_or_get(request: web.Request, params: Any) -> web.Response:
    resp = []
    root_ctx: RootContext = request.app["_root.context"]
    access_key = request["keypair"]["access_key"]

    requester_access_key, owner_access_key = await get_access_key_scopes(request, params)
    log.info(
        "USERCONFIG.LIST_OR_GET (ak:{0}/{1})",
        requester_access_key,
        owner_access_key if owner_access_key != requester_access_key else "*",
    )
    async with root_ctx.db.begin() as conn:
        if params["path"]:
            dotfiles, _ = await query_owned_dotfiles(conn, owner_access_key)
            for dotfile in dotfiles:
                if dotfile["path"] == params["path"]:
                    return web.json_response(dotfile)
            raise DotfileNotFound
        else:
            dotfiles, _ = await query_owned_dotfiles(conn, access_key)
            for entry in dotfiles:
                resp.append({
                    "path": entry["path"],
                    "permission": entry["perm"],
                    "data": entry["data"],
                })
            return web.json_response(resp)


@server_status_required(READ_ALLOWED)
@auth_required
@check_api_params(
    t.Dict(
        {
            t.Key("data"): t.String(max_length=MAXIMUM_DOTFILE_SIZE),
            t.Key("path"): t.String,
            t.Key("permission"): t.Regexp(r"^[0-7]{3}$", re.ASCII),
            t.Key("owner_access_key", default=None): t.Null | t.String,
        },
    )
)
async def update(request: web.Request, params: Any) -> web.Response:
    requester_access_key, owner_access_key = await get_access_key_scopes(request, params)
    log.info(
        "USERCONFIG.CREATE (ak:{0}/{1})",
        requester_access_key,
        owner_access_key if owner_access_key != requester_access_key else "*",
    )
    root_ctx: RootContext = request.app["_root.context"]
    async with root_ctx.db.begin() as conn:
        path: str = params["path"]
        dotfiles, _ = await query_owned_dotfiles(conn, owner_access_key)
        new_dotfiles = [x for x in dotfiles if x["path"] != path]
        if len(new_dotfiles) == len(dotfiles):
            raise DotfileNotFound

        new_dotfiles.append({"path": path, "perm": params["permission"], "data": params["data"]})
        dotfile_packed = msgpack.packb(new_dotfiles)
        if len(dotfile_packed) > MAXIMUM_DOTFILE_SIZE:
            raise DotfileCreationFailed("No leftover space for dotfile storage")

        query = (
            keypairs.update()
            .values(dotfiles=dotfile_packed)
            .where(keypairs.c.access_key == owner_access_key)
        )
        await conn.execute(query)
    return web.json_response({})


@auth_required
@server_status_required(READ_ALLOWED)
@check_api_params(
    t.Dict({
        t.Key("path"): t.String,
        t.Key("owner_access_key", default=None): t.Null | t.String,
    }),
)
async def delete(request: web.Request, params: Any) -> web.Response:
    requester_access_key, owner_access_key = await get_access_key_scopes(request, params)
    log.info(
        "USERCONFIG.DELETE (ak:{0}/{1})",
        requester_access_key,
        owner_access_key if owner_access_key != requester_access_key else "*",
    )
    root_ctx: RootContext = request.app["_root.context"]
    path = params["path"]
    async with root_ctx.db.begin() as conn:
        dotfiles, _ = await query_owned_dotfiles(conn, owner_access_key)
        new_dotfiles = [x for x in dotfiles if x["path"] != path]
        if len(new_dotfiles) == len(dotfiles):
            raise DotfileNotFound
        dotfile_packed = msgpack.packb(new_dotfiles)
        query = (
            keypairs.update()
            .values(dotfiles=dotfile_packed)
            .where(keypairs.c.access_key == owner_access_key)
        )
        await conn.execute(query)
        return web.json_response({"success": True})


@server_status_required(READ_ALLOWED)
@auth_required
@check_api_params(
    t.Dict(
        {
            t.Key("script"): t.String(allow_blank=True, max_length=MAXIMUM_DOTFILE_SIZE),
        },
    )
)
async def update_bootstrap_script(request: web.Request, params: Any) -> web.Response:
    access_key = request["keypair"]["access_key"]
    log.info("UPDATE_BOOTSTRAP_SCRIPT (ak:{0})", access_key)
    root_ctx: RootContext = request.app["_root.context"]
    async with root_ctx.db.begin() as conn:
        script = params.get("script", "").strip()
        if len(script) > MAXIMUM_DOTFILE_SIZE:
            raise DotfileCreationFailed("Maximum bootstrap script length reached")
        query = (
            keypairs.update()
            .values(bootstrap_script=script)
            .where(keypairs.c.access_key == access_key)
        )
        await conn.execute(query)
    return web.json_response({})


@auth_required
@server_status_required(READ_ALLOWED)
async def get_bootstrap_script(request: web.Request) -> web.Response:
    access_key = request["keypair"]["access_key"]
    log.info("USERCONFIG.GET_BOOTSTRAP_SCRIPT (ak:{0})", access_key)
    root_ctx: RootContext = request.app["_root.context"]
    async with root_ctx.db.begin() as conn:
        script, _ = await query_bootstrap_script(conn, access_key)
        return web.json_response(script)


async def init(app: web.Application) -> None:
    pass


async def shutdown(app: web.Application) -> None:
    pass


def create_app(
    default_cors_options: CORSOptions,
) -> Tuple[web.Application, Iterable[WebMiddleware]]:
    app = web.Application()
    app.on_startup.append(init)
    app.on_shutdown.append(shutdown)
    app["api_versions"] = (4, 5)
    app["prefix"] = "user-config"
    cors = aiohttp_cors.setup(app, defaults=default_cors_options)
    cors.add(app.router.add_route("POST", "/dotfiles", create))
    cors.add(app.router.add_route("GET", "/dotfiles", list_or_get))
    cors.add(app.router.add_route("PATCH", "/dotfiles", update))
    cors.add(app.router.add_route("DELETE", "/dotfiles", delete))
    cors.add(app.router.add_route("POST", "/bootstrap-script", update_bootstrap_script))
    cors.add(app.router.add_route("GET", "/bootstrap-script", get_bootstrap_script))

    return app, []
