"""User config handler class using constructor dependency injection.

All handlers use the new ApiHandler pattern: typed parameters
(``BodyParam``, ``QueryParam``, ``UserContext``, ``RequestCtx``) are
automatically extracted by ``_wrap_api_handler`` and responses are
returned as ``APIResponse`` objects.
"""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from ai.backend.common import msgpack
from ai.backend.common.api_handlers import APIResponse, BodyParam, QueryParam
from ai.backend.common.dto.manager.config.request import (
    CreateUserDotfileRequest,
    DeleteUserDotfileRequest,
    GetUserDotfileRequest,
    UpdateBootstrapScriptRequest,
    UpdateUserDotfileRequest,
)
from ai.backend.common.dto.manager.config.response import (
    CreateDotfileResponse,
    DeleteDotfileResponse,
    DotfileItem,
    GetBootstrapScriptResponse,
    GetDotfileResponse,
    ListDotfilesResponse,
    UpdateBootstrapScriptResponse,
    UpdateDotfileResponse,
)
from ai.backend.common.dto.manager.config.types import MAXIMUM_DOTFILE_SIZE
from ai.backend.common.types import AccessKey
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.api.utils import get_access_key_scopes
from ai.backend.manager.dto.context import RequestCtx, UserContext
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.errors.storage import (
    DotfileAlreadyExists,
    DotfileCreationFailed,
    DotfileNotFound,
)
from ai.backend.manager.models.domain import verify_dotfile_name
from ai.backend.manager.models.keypair import keypairs, query_bootstrap_script, query_owned_dotfiles
from ai.backend.manager.models.vfolder import query_accessible_vfolders, vfolders
from ai.backend.manager.services.processors import Processors

if TYPE_CHECKING:
    from ai.backend.manager.api.context import RootContext

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class UserConfigHandler:
    """User config (dotfile) API handler with constructor-injected dependencies."""

    def __init__(self, *, processors: Processors | None = None) -> None:
        self._processors = processors

    async def create(
        self,
        body: BodyParam[CreateUserDotfileRequest],
        ctx: UserContext,
        req: RequestCtx,
    ) -> APIResponse:
        params = body.parsed
        requester_access_key, owner_access_key = await get_access_key_scopes(
            req.request,
            {"owner_access_key": params.owner_access_key},
        )
        log.info(
            "USERCONFIG.CREATE(ak:{}/{})",
            requester_access_key,
            owner_access_key if owner_access_key != requester_access_key else "*",
        )
        root_ctx: RootContext = req.request.app["_root.context"]
        async with root_ctx.db.begin() as conn:
            path = params.path
            dotfiles, leftover_space = await query_owned_dotfiles(conn, owner_access_key)
            if leftover_space == 0:
                raise DotfileCreationFailed("No leftover space for dotfile storage")
            if len(dotfiles) == 100:
                raise DotfileCreationFailed("Dotfile creation limit reached")
            if not verify_dotfile_name(path):
                raise InvalidAPIParameters("dotfile path is reserved for internal operations.")
            duplicate_vfolder = await query_accessible_vfolders(
                conn,
                ctx.user_uuid,
                extra_vf_conds=(vfolders.c.name == path),
            )
            if len(duplicate_vfolder) > 0:
                raise InvalidAPIParameters("dotfile path conflicts with your dot-prefixed vFolder")
            duplicate = [x for x in dotfiles if x["path"] == path]
            if len(duplicate) > 0:
                raise DotfileAlreadyExists
            new_dotfiles = list(dotfiles)
            new_dotfiles.append({"path": path, "perm": params.permission, "data": params.data})
            dotfile_packed = msgpack.packb(new_dotfiles)
            if len(dotfile_packed) > MAXIMUM_DOTFILE_SIZE:
                raise DotfileCreationFailed("No leftover space for dotfile storage")
            query = (
                keypairs.update()
                .values(dotfiles=dotfile_packed)
                .where(keypairs.c.access_key == owner_access_key)
            )
            await conn.execute(query)
        return APIResponse.build(HTTPStatus.OK, CreateDotfileResponse())

    async def list_or_get(
        self,
        query: QueryParam[GetUserDotfileRequest],
        ctx: UserContext,
        req: RequestCtx,
    ) -> APIResponse:
        params = query.parsed
        requester_access_key, owner_access_key = await get_access_key_scopes(
            req.request,
            {"owner_access_key": params.owner_access_key},
        )
        log.info(
            "USERCONFIG.LIST_OR_GET(ak:{}/{})",
            requester_access_key,
            owner_access_key if owner_access_key != requester_access_key else "*",
        )
        root_ctx: RootContext = req.request.app["_root.context"]
        async with root_ctx.db.begin() as conn:
            if params.path:
                dotfiles, _ = await query_owned_dotfiles(conn, owner_access_key)
                for dotfile in dotfiles:
                    if dotfile["path"] == params.path:
                        return APIResponse.build(
                            HTTPStatus.OK,
                            GetDotfileResponse(
                                path=dotfile["path"],
                                perm=dotfile["perm"],
                                data=dotfile["data"],
                            ),
                        )
                raise DotfileNotFound
            dotfiles, _ = await query_owned_dotfiles(conn, AccessKey(ctx.access_key))
            items = [
                DotfileItem(path=entry["path"], perm=entry["perm"], data=entry["data"])
                for entry in dotfiles
            ]
            return APIResponse.build(
                HTTPStatus.OK,
                ListDotfilesResponse(items=items),
            )

    async def update(
        self,
        body: BodyParam[UpdateUserDotfileRequest],
        ctx: UserContext,
        req: RequestCtx,
    ) -> APIResponse:
        params = body.parsed
        requester_access_key, owner_access_key = await get_access_key_scopes(
            req.request,
            {"owner_access_key": params.owner_access_key},
        )
        log.info(
            "USERCONFIG.UPDATE(ak:{}/{})",
            requester_access_key,
            owner_access_key if owner_access_key != requester_access_key else "*",
        )
        root_ctx: RootContext = req.request.app["_root.context"]
        async with root_ctx.db.begin() as conn:
            path = params.path
            dotfiles, _ = await query_owned_dotfiles(conn, owner_access_key)
            new_dotfiles = [x for x in dotfiles if x["path"] != path]
            if len(new_dotfiles) == len(dotfiles):
                raise DotfileNotFound
            new_dotfiles.append({"path": path, "perm": params.permission, "data": params.data})
            dotfile_packed = msgpack.packb(new_dotfiles)
            if len(dotfile_packed) > MAXIMUM_DOTFILE_SIZE:
                raise DotfileCreationFailed("No leftover space for dotfile storage")
            query = (
                keypairs.update()
                .values(dotfiles=dotfile_packed)
                .where(keypairs.c.access_key == owner_access_key)
            )
            await conn.execute(query)
        return APIResponse.build(HTTPStatus.OK, UpdateDotfileResponse())

    async def delete(
        self,
        body: BodyParam[DeleteUserDotfileRequest],
        ctx: UserContext,
        req: RequestCtx,
    ) -> APIResponse:
        params = body.parsed
        requester_access_key, owner_access_key = await get_access_key_scopes(
            req.request,
            {"owner_access_key": params.owner_access_key},
        )
        log.info(
            "USERCONFIG.DELETE(ak:{}/{})",
            requester_access_key,
            owner_access_key if owner_access_key != requester_access_key else "*",
        )
        root_ctx: RootContext = req.request.app["_root.context"]
        async with root_ctx.db.begin() as conn:
            path = params.path
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
        return APIResponse.build(HTTPStatus.OK, DeleteDotfileResponse(success=True))

    async def update_bootstrap_script(
        self,
        body: BodyParam[UpdateBootstrapScriptRequest],
        ctx: UserContext,
        req: RequestCtx,
    ) -> APIResponse:
        params = body.parsed
        log.info("USERCONFIG.UPDATE_BOOTSTRAP_SCRIPT(ak:{})", ctx.access_key)
        root_ctx: RootContext = req.request.app["_root.context"]
        async with root_ctx.db.begin() as conn:
            script = params.script.strip()
            if len(script) > MAXIMUM_DOTFILE_SIZE:
                raise DotfileCreationFailed("Maximum bootstrap script length reached")
            query = (
                keypairs.update()
                .values(bootstrap_script=script)
                .where(keypairs.c.access_key == ctx.access_key)
            )
            await conn.execute(query)
        return APIResponse.build(HTTPStatus.OK, UpdateBootstrapScriptResponse())

    async def get_bootstrap_script(
        self,
        ctx: UserContext,
        req: RequestCtx,
    ) -> APIResponse:
        log.info("USERCONFIG.GET_BOOTSTRAP_SCRIPT(ak:{})", ctx.access_key)
        root_ctx: RootContext = req.request.app["_root.context"]
        async with root_ctx.db.begin() as conn:
            script, _ = await query_bootstrap_script(conn, AccessKey(ctx.access_key))
        return APIResponse.build(
            HTTPStatus.OK,
            GetBootstrapScriptResponse(script=script),
        )
