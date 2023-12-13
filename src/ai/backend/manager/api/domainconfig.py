import logging
import re
from typing import TYPE_CHECKING, Any, Tuple

import aiohttp_cors
import trafaret as t
from aiohttp import web

from ai.backend.common import msgpack
from ai.backend.common.logging import BraceStyleAdapter

from ..models import MAXIMUM_DOTFILE_SIZE, domains, query_domain_dotfiles, verify_dotfile_name
from .auth import admin_required, auth_required
from .exceptions import (
    DomainNotFound,
    DotfileAlreadyExists,
    DotfileCreationFailed,
    DotfileNotFound,
    GenericForbidden,
    InvalidAPIParameters,
)
from .manager import READ_ALLOWED, server_status_required
from .types import CORSOptions, Iterable, WebMiddleware
from .utils import check_api_params

if TYPE_CHECKING:
    from .context import RootContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


@server_status_required(READ_ALLOWED)
@admin_required
@check_api_params(
    t.Dict(
        {
            t.Key("domain"): t.String,
            t.Key("data"): t.String(max_length=MAXIMUM_DOTFILE_SIZE),
            t.Key("path"): t.String,
            t.Key("permission"): t.Regexp(r"^[0-7]{3}$", re.ASCII),
        },
    )
)
async def create(request: web.Request, params: Any) -> web.Response:
    log.info("DOMAINCOFNIG.CREATE_DOTFILE (domain: {0})", params["domain"])
    if not request["is_superadmin"] and request["user"]["domain_name"] != params["domain"]:
        raise GenericForbidden("Domain admins cannot create dotfiles of other domains")
    root_ctx: RootContext = request.app["_root.context"]
    async with root_ctx.db.begin() as conn:
        dotfiles, leftover_space = await query_domain_dotfiles(conn, params["domain"])
        if dotfiles is None:
            raise DomainNotFound("Input domain is not found")
        if leftover_space == 0:
            raise DotfileCreationFailed("No leftover space for dotfile storage")
        if len(dotfiles) == 100:
            raise DotfileCreationFailed("Dotfile creation limit reached")
        if not verify_dotfile_name(params["path"]):
            raise InvalidAPIParameters("dotfile path is reserved for internal operations.")

        duplicate = [x for x in dotfiles if x["path"] == params["path"]]
        if len(duplicate) > 0:
            raise DotfileAlreadyExists
        new_dotfiles = list(dotfiles)
        new_dotfiles.append({
            "path": params["path"],
            "perm": params["permission"],
            "data": params["data"],
        })
        dotfile_packed = msgpack.packb(new_dotfiles)
        if len(dotfile_packed) > MAXIMUM_DOTFILE_SIZE:
            raise DotfileCreationFailed("No leftover space for dotfile storage")

        query = (
            domains.update()
            .values(dotfiles=dotfile_packed)
            .where(domains.c.name == params["domain"])
        )
        await conn.execute(query)
    return web.json_response({})


@server_status_required(READ_ALLOWED)
@auth_required
@check_api_params(
    t.Dict({
        t.Key("domain"): t.String,
        t.Key("path", default=None): t.Null | t.String,
    })
)
async def list_or_get(request: web.Request, params: Any) -> web.Response:
    log.info("DOMAINCONFIG.LIST_OR_GET_DOTFILE (domain: {0})", params["domain"])
    if not request["is_superadmin"] and request["user"]["domain_name"] != params["domain"]:
        raise GenericForbidden("Users cannot access dotfiles of other domains")
    resp = []
    root_ctx: RootContext = request.app["_root.context"]
    async with root_ctx.db.begin() as conn:
        if params["path"]:
            dotfiles, _ = await query_domain_dotfiles(conn, params["domain"])
            if dotfiles is None:
                raise DomainNotFound
            for dotfile in dotfiles:
                if dotfile["path"] == params["path"]:
                    return web.json_response(dotfile)
            raise DotfileNotFound
        else:
            dotfiles, _ = await query_domain_dotfiles(conn, params["domain"])
            if dotfiles is None:
                raise DomainNotFound
            for entry in dotfiles:
                resp.append({
                    "path": entry["path"],
                    "permission": entry["perm"],
                    "data": entry["data"],
                })
            return web.json_response(resp)


@server_status_required(READ_ALLOWED)
@admin_required
@check_api_params(
    t.Dict(
        {
            t.Key("domain"): t.String,
            t.Key("data"): t.String(max_length=MAXIMUM_DOTFILE_SIZE),
            t.Key("path"): t.String,
            t.Key("permission"): t.Regexp(r"^[0-7]{3}$", re.ASCII),
        },
    )
)
async def update(request: web.Request, params: Any) -> web.Response:
    log.info("DOMAINCONFIG.UPDATE_DOTFILE (domain:{0})", params["domain"])
    if not request["is_superadmin"] and request["user"]["domain_name"] != params["domain"]:
        raise GenericForbidden("Domain admins cannot update dotfiles of other domains")
    root_ctx: RootContext = request.app["_root.context"]
    async with root_ctx.db.begin() as conn:
        dotfiles, _ = await query_domain_dotfiles(conn, params["domain"])
        if dotfiles is None:
            raise DomainNotFound
        new_dotfiles = [x for x in dotfiles if x["path"] != params["path"]]
        if len(new_dotfiles) == len(dotfiles):
            raise DotfileNotFound

        new_dotfiles.append({
            "path": params["path"],
            "perm": params["permission"],
            "data": params["data"],
        })
        dotfile_packed = msgpack.packb(new_dotfiles)
        if len(dotfile_packed) > MAXIMUM_DOTFILE_SIZE:
            raise DotfileCreationFailed("No leftover space for dotfile storage")

        query = (
            domains.update()
            .values(dotfiles=dotfile_packed)
            .where(domains.c.name == params["domain"])
        )
        await conn.execute(query)
    return web.json_response({})


@server_status_required(READ_ALLOWED)
@admin_required
@check_api_params(
    t.Dict({
        t.Key("domain"): t.String,
        t.Key("path"): t.String,
    }),
)
async def delete(request: web.Request, params: Any) -> web.Response:
    log.info("DOMAINCONFIG.DELETE_DOTFILE (domain:{0})", params["domain"])
    if not request["is_superadmin"] and request["user"]["domain_name"] != params["domain"]:
        raise GenericForbidden("Domain admins cannot delete dotfiles of other domains")
    root_ctx: RootContext = request.app["_root.context"]
    async with root_ctx.db.begin() as conn:
        dotfiles, _ = await query_domain_dotfiles(conn, params["domain"])
        if dotfiles is None:
            raise DomainNotFound
        new_dotfiles = [x for x in dotfiles if x["path"] != params["path"]]
        if len(new_dotfiles) == len(dotfiles):
            raise DotfileNotFound

        dotfile_packed = msgpack.packb(new_dotfiles)
        query = (
            domains.update()
            .values(dotfiles=dotfile_packed)
            .where(domains.c.name == params["domain"])
        )
        await conn.execute(query)
        return web.json_response({"success": True})


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
    app["prefix"] = "domain-config"
    cors = aiohttp_cors.setup(app, defaults=default_cors_options)
    cors.add(app.router.add_route("POST", "/dotfiles", create))
    cors.add(app.router.add_route("GET", "/dotfiles", list_or_get))
    cors.add(app.router.add_route("PATCH", "/dotfiles", update))
    cors.add(app.router.add_route("DELETE", "/dotfiles", delete))

    return app, []
