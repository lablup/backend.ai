import logging
import re
from typing import TYPE_CHECKING, Any, Tuple

import aiohttp_cors
import sqlalchemy as sa
import trafaret as t
from aiohttp import web

from ai.backend.common import msgpack
from ai.backend.common import validators as tx
from ai.backend.common.logging import BraceStyleAdapter

from ..models import (
    MAXIMUM_DOTFILE_SIZE,
    groups,
    query_group_domain,
    query_group_dotfiles,
    verify_dotfile_name,
)
from ..models import association_groups_users as agus
from .auth import admin_required, auth_required
from .exceptions import (
    DotfileAlreadyExists,
    DotfileCreationFailed,
    DotfileNotFound,
    GenericForbidden,
    GroupNotFound,
    InvalidAPIParameters,
)
from .manager import READ_ALLOWED, server_status_required
from .types import CORSOptions, Iterable, WebMiddleware
from .utils import check_api_params

if TYPE_CHECKING:
    from .context import RootContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@server_status_required(READ_ALLOWED)
@admin_required
@check_api_params(
    t.Dict(
        {
            tx.AliasedKey(["group", "groupId", "group_id"]): tx.UUID | t.String,
            t.Key("domain", default=None): t.String | t.Null,
            t.Key("data"): t.String(max_length=MAXIMUM_DOTFILE_SIZE),
            t.Key("path"): t.String,
            t.Key("permission"): t.Regexp(r"^[0-7]{3}$", re.ASCII),
        },
    )
)
async def create(request: web.Request, params: Any) -> web.Response:
    log.info("GROUPCONFIG.CREATE_DOTFILE (group: {0})", params["group"])
    root_ctx: RootContext = request.app["_root.context"]
    group_id_or_name = params["group"]
    async with root_ctx.db.begin() as conn:
        if isinstance(group_id_or_name, str):
            if params["domain"] is None:
                raise InvalidAPIParameters("Missing parameter 'domain'")

            query = (
                sa.select([groups.c.id])
                .select_from(groups)
                .where(groups.c.domain_name == params["domain"])
                .where(groups.c.name == group_id_or_name)
            )
            group_id = await conn.scalar(query)
            domain = params["domain"]
        else:
            group_id = group_id_or_name
            # if group UUID is given, override input domain
            domain = await query_group_domain(conn, group_id)
        if group_id is None or domain is None:
            raise GroupNotFound
        if not request["is_superadmin"] and request["user"]["domain_name"] != domain:
            raise GenericForbidden("Admins cannot create group dotfiles of other domains")

        dotfiles, leftover_space = await query_group_dotfiles(conn, group_id)
        if dotfiles is None:
            raise GroupNotFound
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

        query = groups.update().values(dotfiles=dotfile_packed).where(groups.c.id == group_id)
        await conn.execute(query)
    return web.json_response({})


@server_status_required(READ_ALLOWED)
@auth_required
@check_api_params(
    t.Dict({
        tx.AliasedKey(["group", "groupId", "group_id"]): tx.UUID | t.String,
        t.Key("domain", default=None): t.String | t.Null,
        t.Key("path", default=None): t.Null | t.String,
    })
)
async def list_or_get(request: web.Request, params: Any) -> web.Response:
    log.info("GROUPCONFIG.LIST_OR_GET_DOTFILE (group: {0})", params["group"])
    root_ctx: RootContext = request.app["_root.context"]
    resp = []
    group_id_or_name = params["group"]
    async with root_ctx.db.begin() as conn:
        if isinstance(group_id_or_name, str):
            if params["domain"] is None:
                raise InvalidAPIParameters("Missing parameter 'domain'")
            query = (
                sa.select([groups.c.id])
                .select_from(groups)
                .where(groups.c.domain_name == params["domain"])
                .where(groups.c.name == group_id_or_name)
            )
            group_id = await conn.scalar(query)
            domain = params["domain"]
        else:
            group_id = group_id_or_name
            domain = await query_group_domain(conn, group_id)
        if group_id is None or domain is None:
            raise GroupNotFound
        if not request["is_superadmin"]:
            if request["is_admin"]:
                if request["user"]["domain_name"] != domain:
                    raise GenericForbidden(
                        "Domain admins cannot access group dotfiles of other domains"
                    )
            else:
                # check if user (non-admin) is in the group
                query = (
                    sa.select([agus.c.group_id])
                    .select_from(agus)
                    .where(agus.c.user_id == request["user"]["uuid"])
                )
                result = await conn.execute(query)
                rows = result.fetchall()
                if group_id not in map(lambda x: x.group_id, rows):
                    raise GenericForbidden("Users cannot access group dotfiles of other groups")

        if params["path"]:
            dotfiles, _ = await query_group_dotfiles(conn, group_id)
            if dotfiles is None:
                raise GroupNotFound
            for dotfile in dotfiles:
                if dotfile["path"] == params["path"]:
                    return web.json_response(dotfile)
            raise DotfileNotFound
        else:
            dotfiles, _ = await query_group_dotfiles(conn, group_id)
            if dotfiles is None:
                raise GroupNotFound
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
            tx.AliasedKey(["group", "groupId", "group_id"]): tx.UUID | t.String,
            t.Key("domain", default=None): t.String | t.Null,
            t.Key("data"): t.String(max_length=MAXIMUM_DOTFILE_SIZE),
            t.Key("path"): t.String,
            t.Key("permission"): t.Regexp(r"^[0-7]{3}$", re.ASCII),
        },
    )
)
async def update(request: web.Request, params: Any) -> web.Response:
    log.info("GROUPCONFIG.UPDATE_DOTFILE (domain:{0})", params["domain"])
    root_ctx: RootContext = request.app["_root.context"]
    group_id_or_name = params["group"]
    async with root_ctx.db.begin() as conn:
        if isinstance(group_id_or_name, str):
            if params["domain"] is None:
                raise InvalidAPIParameters("Missing parameter 'domain'")
            query = (
                sa.select([groups.c.id])
                .select_from(groups)
                .where(groups.c.domain_name == params["domain"])
                .where(groups.c.name == group_id_or_name)
            )
            group_id = await conn.scalar(query)
            domain = params["domain"]
        else:
            group_id = group_id_or_name
            domain = await query_group_domain(conn, group_id)
        if group_id is None or domain is None:
            raise GroupNotFound
        if not request["is_superadmin"] and request["user"]["domain_name"] != domain:
            raise GenericForbidden("Admins cannot update group dotfiles of other domains")

        dotfiles, _ = await query_group_dotfiles(conn, group_id)
        if dotfiles is None:
            raise GroupNotFound
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

        query = groups.update().values(dotfiles=dotfile_packed).where(groups.c.id == group_id)
        await conn.execute(query)
    return web.json_response({})


@server_status_required(READ_ALLOWED)
@admin_required
@check_api_params(
    t.Dict({
        tx.AliasedKey(["group", "groupId", "group_id"]): tx.UUID | t.String,
        t.Key("domain", default=None): t.String | t.Null,
        t.Key("path"): t.String,
    }),
)
async def delete(request: web.Request, params: Any) -> web.Response:
    log.info("GROUPCONFIG.DELETE_DOTFILE (domain:{0})", params["domain"])
    root_ctx: RootContext = request.app["_root.context"]
    group_id_or_name = params["group"]
    async with root_ctx.db.begin() as conn:
        if isinstance(group_id_or_name, str):
            if params["domain"] is None:
                raise InvalidAPIParameters("Missing parameter 'domain'")
            query = (
                sa.select([groups.c.id])
                .select_from(groups)
                .where(groups.c.domain_name == params["domain"])
                .where(groups.c.name == group_id_or_name)
            )
            group_id = await conn.scalar(query)
            domain = params["domain"]
        else:
            group_id = group_id_or_name
            domain = await query_group_domain(conn, group_id)
        if group_id is None or domain is None:
            raise GroupNotFound
        if not request["is_superadmin"] and request["user"]["domain_name"] != domain:
            raise GenericForbidden("Admins cannot delete dotfiles of other domains")

        dotfiles, _ = await query_group_dotfiles(conn, group_id)
        if dotfiles is None:
            raise DotfileNotFound
        new_dotfiles = [x for x in dotfiles if x["path"] != params["path"]]
        if len(new_dotfiles) == len(dotfiles):
            raise DotfileNotFound

        dotfile_packed = msgpack.packb(new_dotfiles)
        query = groups.update().values(dotfiles=dotfile_packed).where(groups.c.id == group_id)
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
    app["prefix"] = "group-config"
    cors = aiohttp_cors.setup(app, defaults=default_cors_options)
    cors.add(app.router.add_route("POST", "/dotfiles", create))
    cors.add(app.router.add_route("GET", "/dotfiles", list_or_get))
    cors.add(app.router.add_route("PATCH", "/dotfiles", update))
    cors.add(app.router.add_route("DELETE", "/dotfiles", delete))

    return app, []
