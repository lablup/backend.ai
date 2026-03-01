"""User config handler class using constructor dependency injection.

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
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.api.utils import get_access_key_scopes
from ai.backend.manager.data.dotfile.types import DotfileScope
from ai.backend.manager.dto.context import RequestCtx, UserContext
from ai.backend.manager.services.dotfile import (
    CreateDotfileAction,
    DeleteDotfileAction,
    GetBootstrapScriptAction,
    ListOrGetDotfilesAction,
    UpdateBootstrapScriptAction,
    UpdateDotfileAction,
)
from ai.backend.manager.services.processors import Processors

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class UserConfigHandler:
    """User config (dotfile) API handler with constructor-injected dependencies."""

    def __init__(self, *, processors: Processors) -> None:
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
        action = CreateDotfileAction(
            scope=DotfileScope.USER,
            entity_key=owner_access_key,
            path=params.path,
            data=params.data,
            permission=params.permission,
            user_uuid=ctx.user_uuid,
        )
        await self._processors.dotfile.create.wait_for_complete(action)
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
        action = ListOrGetDotfilesAction(
            scope=DotfileScope.USER,
            entity_key=owner_access_key,
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
        action = UpdateDotfileAction(
            scope=DotfileScope.USER,
            entity_key=owner_access_key,
            path=params.path,
            data=params.data,
            permission=params.permission,
        )
        await self._processors.dotfile.update.wait_for_complete(action)
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
        action = DeleteDotfileAction(
            scope=DotfileScope.USER,
            entity_key=owner_access_key,
            path=params.path,
        )
        await self._processors.dotfile.delete.wait_for_complete(action)
        return APIResponse.build(HTTPStatus.OK, DeleteDotfileResponse(success=True))

    async def update_bootstrap_script(
        self,
        body: BodyParam[UpdateBootstrapScriptRequest],
        ctx: UserContext,
    ) -> APIResponse:
        params = body.parsed
        log.info("USERCONFIG.UPDATE_BOOTSTRAP_SCRIPT(ak:{})", ctx.access_key)
        action = UpdateBootstrapScriptAction(
            access_key=ctx.access_key,
            script=params.script,
        )
        await self._processors.dotfile.update_bootstrap.wait_for_complete(action)
        return APIResponse.build(HTTPStatus.OK, UpdateBootstrapScriptResponse())

    async def get_bootstrap_script(
        self,
        ctx: UserContext,
    ) -> APIResponse:
        log.info("USERCONFIG.GET_BOOTSTRAP_SCRIPT(ak:{})", ctx.access_key)
        action = GetBootstrapScriptAction(access_key=ctx.access_key)
        result = await self._processors.dotfile.get_bootstrap.wait_for_complete(action)
        return APIResponse.build(
            HTTPStatus.OK,
            GetBootstrapScriptResponse(script=result.script),
        )
