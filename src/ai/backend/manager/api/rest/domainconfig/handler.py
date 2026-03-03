"""Domain config handler class using constructor dependency injection.

All handlers use the new ApiHandler pattern: typed parameters
(``BodyParam``, ``QueryParam``, ``UserContext``, ``RequestCtx``) are
automatically extracted by ``_wrap_api_handler`` and responses are
returned as ``APIResponse`` objects.
"""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import Final

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
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.dotfile.types import DotfileScope
from ai.backend.manager.dto.context import UserContext
from ai.backend.manager.errors.common import GenericForbidden
from ai.backend.manager.services.dotfile import (
    CreateDotfileAction,
    DeleteDotfileAction,
    ListOrGetDotfilesAction,
    UpdateDotfileAction,
)
from ai.backend.manager.services.processors import Processors

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class DomainConfigHandler:
    """Domain config (dotfile) API handler with constructor-injected dependencies."""

    def __init__(self, *, processors: Processors) -> None:
        self._processors = processors

    async def create(
        self,
        body: BodyParam[CreateDomainDotfileRequest],
        ctx: UserContext,
    ) -> APIResponse:
        params = body.parsed
        log.info("DOMAINCONFIG.CREATE(domain:{})", params.domain)
        if not ctx.is_superadmin and ctx.user_domain != params.domain:
            raise GenericForbidden("Domain admins cannot create dotfiles of other domains")
        action = CreateDotfileAction(
            scope=DotfileScope.DOMAIN,
            entity_key=params.domain,
            path=params.path,
            data=params.data,
            permission=params.permission,
        )
        await self._processors.dotfile.create.wait_for_complete(action)
        return APIResponse.build(HTTPStatus.OK, CreateDotfileResponse())

    async def list_or_get(
        self,
        query: QueryParam[GetDomainDotfileRequest],
        ctx: UserContext,
    ) -> APIResponse:
        params = query.parsed
        log.info("DOMAINCONFIG.LIST_OR_GET(domain:{})", params.domain)
        if not ctx.is_superadmin and ctx.user_domain != params.domain:
            raise GenericForbidden("Users cannot access dotfiles of other domains")
        action = ListOrGetDotfilesAction(
            scope=DotfileScope.DOMAIN,
            entity_key=params.domain,
            path=params.path,
        )
        result = await self._processors.dotfile.list_or_get.wait_for_complete(action)
        if params.path:
            entry = result.entries[0]
            return APIResponse.build(
                HTTPStatus.OK,
                GetDotfileResponse(path=entry.path, perm=entry.perm, data=entry.data),
            )
        items = [DotfileItem(path=e.path, perm=e.perm, data=e.data) for e in result.entries]
        return APIResponse.build(HTTPStatus.OK, ListDotfilesResponse(items=items))

    async def update(
        self,
        body: BodyParam[UpdateDomainDotfileRequest],
        ctx: UserContext,
    ) -> APIResponse:
        params = body.parsed
        log.info("DOMAINCONFIG.UPDATE(domain:{})", params.domain)
        if not ctx.is_superadmin and ctx.user_domain != params.domain:
            raise GenericForbidden("Domain admins cannot update dotfiles of other domains")
        action = UpdateDotfileAction(
            scope=DotfileScope.DOMAIN,
            entity_key=params.domain,
            path=params.path,
            data=params.data,
            permission=params.permission,
        )
        await self._processors.dotfile.update.wait_for_complete(action)
        return APIResponse.build(HTTPStatus.OK, UpdateDotfileResponse())

    async def delete(
        self,
        query: QueryParam[DeleteDomainDotfileRequest],
        ctx: UserContext,
    ) -> APIResponse:
        params = query.parsed
        log.info("DOMAINCONFIG.DELETE(domain:{})", params.domain)
        if not ctx.is_superadmin and ctx.user_domain != params.domain:
            raise GenericForbidden("Domain admins cannot delete dotfiles of other domains")
        action = DeleteDotfileAction(
            scope=DotfileScope.DOMAIN,
            entity_key=params.domain,
            path=params.path,
        )
        await self._processors.dotfile.delete.wait_for_complete(action)
        return APIResponse.build(HTTPStatus.OK, DeleteDotfileResponse(success=True))
