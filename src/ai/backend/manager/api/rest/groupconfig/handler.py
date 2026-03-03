"""Group config handler class using constructor dependency injection.

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
    CreateGroupDotfileRequest,
    DeleteGroupDotfileRequest,
    GetGroupDotfileRequest,
    UpdateGroupDotfileRequest,
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
    CheckGroupMembershipAction,
    CreateDotfileAction,
    DeleteDotfileAction,
    ListOrGetDotfilesAction,
    ResolveGroupAction,
    UpdateDotfileAction,
)
from ai.backend.manager.services.processors import Processors

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class GroupConfigHandler:
    """Group config (dotfile) API handler with constructor-injected dependencies."""

    def __init__(self, *, processors: Processors) -> None:
        self._processors = processors

    async def create(
        self,
        body: BodyParam[CreateGroupDotfileRequest],
        ctx: UserContext,
    ) -> APIResponse:
        params = body.parsed
        log.info("GROUPCONFIG.CREATE(group:{})", params.group)
        resolve_result = await self._processors.dotfile.resolve_group.wait_for_complete(
            ResolveGroupAction(
                group_id_or_name=params.group,
                group_domain=params.domain,
                user_domain=ctx.user_domain,
            )
        )
        if not ctx.is_superadmin and ctx.user_domain != resolve_result.domain:
            raise GenericForbidden("Admins cannot create group dotfiles of other domains")
        action = CreateDotfileAction(
            scope=DotfileScope.GROUP,
            entity_key=resolve_result.group_id,
            path=params.path,
            data=params.data,
            permission=params.permission,
        )
        await self._processors.dotfile.create.wait_for_complete(action)
        return APIResponse.build(HTTPStatus.OK, CreateDotfileResponse())

    async def list_or_get(
        self,
        query: QueryParam[GetGroupDotfileRequest],
        ctx: UserContext,
    ) -> APIResponse:
        params = query.parsed
        log.info("GROUPCONFIG.LIST_OR_GET(group:{})", params.group)
        resolve_result = await self._processors.dotfile.resolve_group.wait_for_complete(
            ResolveGroupAction(
                group_id_or_name=params.group,
                group_domain=params.domain,
                user_domain=ctx.user_domain,
            )
        )
        if not ctx.is_superadmin:
            if ctx.is_admin:
                if ctx.user_domain != resolve_result.domain:
                    raise GenericForbidden(
                        "Domain admins cannot access group dotfiles of other domains"
                    )
            else:
                membership = (
                    await self._processors.dotfile.check_group_membership.wait_for_complete(
                        CheckGroupMembershipAction(user_uuid=ctx.user_uuid)
                    )
                )
                if resolve_result.group_id not in membership.group_ids:
                    raise GenericForbidden("Users cannot access group dotfiles of other groups")
        action = ListOrGetDotfilesAction(
            scope=DotfileScope.GROUP,
            entity_key=resolve_result.group_id,
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
        body: BodyParam[UpdateGroupDotfileRequest],
        ctx: UserContext,
    ) -> APIResponse:
        params = body.parsed
        log.info("GROUPCONFIG.UPDATE(group:{})", params.group)
        resolve_result = await self._processors.dotfile.resolve_group.wait_for_complete(
            ResolveGroupAction(
                group_id_or_name=params.group,
                group_domain=params.domain,
                user_domain=ctx.user_domain,
            )
        )
        if not ctx.is_superadmin and ctx.user_domain != resolve_result.domain:
            raise GenericForbidden("Admins cannot update group dotfiles of other domains")
        action = UpdateDotfileAction(
            scope=DotfileScope.GROUP,
            entity_key=resolve_result.group_id,
            path=params.path,
            data=params.data,
            permission=params.permission,
        )
        await self._processors.dotfile.update.wait_for_complete(action)
        return APIResponse.build(HTTPStatus.OK, UpdateDotfileResponse())

    async def delete(
        self,
        query: QueryParam[DeleteGroupDotfileRequest],
        ctx: UserContext,
    ) -> APIResponse:
        params = query.parsed
        log.info("GROUPCONFIG.DELETE(group:{})", params.group)
        resolve_result = await self._processors.dotfile.resolve_group.wait_for_complete(
            ResolveGroupAction(
                group_id_or_name=params.group,
                group_domain=params.domain,
                user_domain=ctx.user_domain,
            )
        )
        if not ctx.is_superadmin and ctx.user_domain != resolve_result.domain:
            raise GenericForbidden("Admins cannot delete dotfiles of other domains")
        action = DeleteDotfileAction(
            scope=DotfileScope.GROUP,
            entity_key=resolve_result.group_id,
            path=params.path,
        )
        await self._processors.dotfile.delete.wait_for_complete(action)
        return APIResponse.build(HTTPStatus.OK, DeleteDotfileResponse(success=True))
