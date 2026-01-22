import logging
import re
from typing import TYPE_CHECKING, Any

import aiohttp_cors
import trafaret as t
from aiohttp import web

from ai.backend.common import validators as tx
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.models.domain import MAXIMUM_DOTFILE_SIZE
from ai.backend.manager.services.group_config.actions.create_dotfile import CreateDotfileAction
from ai.backend.manager.services.group_config.actions.delete_dotfile import DeleteDotfileAction
from ai.backend.manager.services.group_config.actions.get_dotfile import GetDotfileAction
from ai.backend.manager.services.group_config.actions.list_dotfiles import ListDotfilesAction
from ai.backend.manager.services.group_config.actions.update_dotfile import UpdateDotfileAction

from .auth import admin_required, auth_required
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

    action = CreateDotfileAction(
        group_id_or_name=params["group"],
        domain_name=params["domain"],
        path=params["path"],
        data=params["data"],
        permission=params["permission"],
    )
    await root_ctx.processors.group_config.create_dotfile.wait_for_complete(action)
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

    if params["path"]:
        get_action = GetDotfileAction(
            group_id_or_name=params["group"],
            domain_name=params["domain"],
            path=params["path"],
        )
        get_result = await root_ctx.processors.group_config.get_dotfile.wait_for_complete(
            get_action
        )
        return web.json_response(get_result.dotfile)

    list_action = ListDotfilesAction(
        group_id_or_name=params["group"],
        domain_name=params["domain"],
    )
    list_result = await root_ctx.processors.group_config.list_dotfiles.wait_for_complete(
        list_action
    )
    # Transform response format for API compatibility
    resp = [
        {
            "path": entry["path"],
            "permission": entry["perm"],
            "data": entry["data"],
        }
        for entry in list_result.dotfiles
    ]
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

    action = UpdateDotfileAction(
        group_id_or_name=params["group"],
        domain_name=params["domain"],
        path=params["path"],
        data=params["data"],
        permission=params["permission"],
    )
    await root_ctx.processors.group_config.update_dotfile.wait_for_complete(action)
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

    action = DeleteDotfileAction(
        group_id_or_name=params["group"],
        domain_name=params["domain"],
        path=params["path"],
    )
    result = await root_ctx.processors.group_config.delete_dotfile.wait_for_complete(action)
    return web.json_response({"success": result.success})


async def init(app: web.Application) -> None:
    pass


async def shutdown(app: web.Application) -> None:
    pass


def create_app(
    default_cors_options: CORSOptions,
) -> tuple[web.Application, Iterable[WebMiddleware]]:
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
