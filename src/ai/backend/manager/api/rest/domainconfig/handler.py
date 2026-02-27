"""Domain config handler class using constructor dependency injection.

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
    CreateDomainDotfileRequest,
    DeleteDomainDotfileRequest,
    GetDomainDotfileRequest,
    UpdateDomainDotfileRequest,
)
from ai.backend.common.dto.manager.config.response import (
    CreateDotfileResponse,
    DeleteDotfileResponse,
    DotfileItem,
    GetDotfileResponse,
    ListDotfilesResponse,
    UpdateDotfileResponse,
)
from ai.backend.common.dto.manager.config.types import MAXIMUM_DOTFILE_SIZE
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.dto.context import RequestCtx, UserContext
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.errors.common import GenericForbidden
from ai.backend.manager.errors.resource import DomainNotFound
from ai.backend.manager.errors.storage import (
    DotfileAlreadyExists,
    DotfileCreationFailed,
    DotfileNotFound,
)
from ai.backend.manager.models.domain import (
    domains,
    query_domain_dotfiles,
    verify_dotfile_name,
)
from ai.backend.manager.services.processors import Processors

if TYPE_CHECKING:
    from ai.backend.manager.api.context import RootContext

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class DomainConfigHandler:
    """Domain config (dotfile) API handler with constructor-injected dependencies."""

    def __init__(self, *, processors: Processors | None = None) -> None:
        self._processors = processors

    async def create(
        self,
        body: BodyParam[CreateDomainDotfileRequest],
        ctx: UserContext,
        req: RequestCtx,
    ) -> APIResponse:
        params = body.parsed
        log.info("DOMAINCONFIG.CREATE(domain:{})", params.domain)
        if not ctx.is_superadmin and ctx.user_domain != params.domain:
            raise GenericForbidden("Domain admins cannot create dotfiles of other domains")
        root_ctx: RootContext = req.request.app["_root.context"]
        async with root_ctx.db.begin() as conn:
            dotfiles, leftover_space = await query_domain_dotfiles(conn, params.domain)
            if dotfiles is None:
                raise DomainNotFound("Input domain is not found")
            if leftover_space == 0:
                raise DotfileCreationFailed("No leftover space for dotfile storage")
            if len(dotfiles) == 100:
                raise DotfileCreationFailed("Dotfile creation limit reached")
            if not verify_dotfile_name(params.path):
                raise InvalidAPIParameters("dotfile path is reserved for internal operations.")
            duplicate = [x for x in dotfiles if x["path"] == params.path]
            if len(duplicate) > 0:
                raise DotfileAlreadyExists
            new_dotfiles = list(dotfiles)
            new_dotfiles.append({
                "path": params.path,
                "perm": params.permission,
                "data": params.data,
            })
            dotfile_packed = msgpack.packb(new_dotfiles)
            if len(dotfile_packed) > MAXIMUM_DOTFILE_SIZE:
                raise DotfileCreationFailed("No leftover space for dotfile storage")
            query = (
                domains.update()
                .values(dotfiles=dotfile_packed)
                .where(domains.c.name == params.domain)
            )
            await conn.execute(query)
        return APIResponse.build(HTTPStatus.OK, CreateDotfileResponse())

    async def list_or_get(
        self,
        query: QueryParam[GetDomainDotfileRequest],
        ctx: UserContext,
        req: RequestCtx,
    ) -> APIResponse:
        params = query.parsed
        log.info("DOMAINCONFIG.LIST_OR_GET(domain:{})", params.domain)
        if not ctx.is_superadmin and ctx.user_domain != params.domain:
            raise GenericForbidden("Users cannot access dotfiles of other domains")
        root_ctx: RootContext = req.request.app["_root.context"]
        async with root_ctx.db.begin() as conn:
            if params.path:
                dotfiles, _ = await query_domain_dotfiles(conn, params.domain)
                if dotfiles is None:
                    raise DomainNotFound
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
            dotfiles, _ = await query_domain_dotfiles(conn, params.domain)
            if dotfiles is None:
                raise DomainNotFound
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
        body: BodyParam[UpdateDomainDotfileRequest],
        ctx: UserContext,
        req: RequestCtx,
    ) -> APIResponse:
        params = body.parsed
        log.info("DOMAINCONFIG.UPDATE(domain:{})", params.domain)
        if not ctx.is_superadmin and ctx.user_domain != params.domain:
            raise GenericForbidden("Domain admins cannot update dotfiles of other domains")
        root_ctx: RootContext = req.request.app["_root.context"]
        async with root_ctx.db.begin() as conn:
            dotfiles, _ = await query_domain_dotfiles(conn, params.domain)
            if dotfiles is None:
                raise DomainNotFound
            new_dotfiles = [x for x in dotfiles if x["path"] != params.path]
            if len(new_dotfiles) == len(dotfiles):
                raise DotfileNotFound
            new_dotfiles.append({
                "path": params.path,
                "perm": params.permission,
                "data": params.data,
            })
            dotfile_packed = msgpack.packb(new_dotfiles)
            if len(dotfile_packed) > MAXIMUM_DOTFILE_SIZE:
                raise DotfileCreationFailed("No leftover space for dotfile storage")
            query = (
                domains.update()
                .values(dotfiles=dotfile_packed)
                .where(domains.c.name == params.domain)
            )
            await conn.execute(query)
        return APIResponse.build(HTTPStatus.OK, UpdateDotfileResponse())

    async def delete(
        self,
        body: BodyParam[DeleteDomainDotfileRequest],
        ctx: UserContext,
        req: RequestCtx,
    ) -> APIResponse:
        params = body.parsed
        log.info("DOMAINCONFIG.DELETE(domain:{})", params.domain)
        if not ctx.is_superadmin and ctx.user_domain != params.domain:
            raise GenericForbidden("Domain admins cannot delete dotfiles of other domains")
        root_ctx: RootContext = req.request.app["_root.context"]
        async with root_ctx.db.begin() as conn:
            dotfiles, _ = await query_domain_dotfiles(conn, params.domain)
            if dotfiles is None:
                raise DomainNotFound
            new_dotfiles = [x for x in dotfiles if x["path"] != params.path]
            if len(new_dotfiles) == len(dotfiles):
                raise DotfileNotFound
            dotfile_packed = msgpack.packb(new_dotfiles)
            query = (
                domains.update()
                .values(dotfiles=dotfile_packed)
                .where(domains.c.name == params.domain)
            )
            await conn.execute(query)
        return APIResponse.build(HTTPStatus.OK, DeleteDotfileResponse(success=True))
