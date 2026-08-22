"""User config handler class using constructor dependency injection.

A keypair's dotfiles and bootstrap script are columns of the keypair row, which
belongs to a user, so every operation here is answered for by that user.
"""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import Final

from ai.backend.common.api_handlers import APIResponse, BodyParam, QueryParam
from ai.backend.common.data.entity.user import UserID
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
    DotfileListItem,
    GetBootstrapScriptResponse,
    GetDotfileResponse,
    ListDotfilesResponse,
    UpdateBootstrapScriptResponse,
    UpdateDotfileResponse,
)
from ai.backend.common.types import AccessKey
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.dotfile.types import DotfileEntries, DotfileEntry
from ai.backend.manager.dto.context import UserContext
from ai.backend.manager.services.auth.actions.resolve_access_key_scope import (
    ResolveAccessKeyScopeAction,
)
from ai.backend.manager.services.auth.processors import AuthProcessors
from ai.backend.manager.services.user.actions.bootstrap_script import (
    GetBootstrapScriptAction,
    UpdateBootstrapScriptAction,
)
from ai.backend.manager.services.user.actions.create_keypair_dotfile import (
    CreateKeypairDotfileAction,
)
from ai.backend.manager.services.user.actions.delete_keypair_dotfile import (
    DeleteKeypairDotfileAction,
)
from ai.backend.manager.services.user.actions.keypair_ops import AdminGetKeypairAction
from ai.backend.manager.services.user.actions.lookup_keypair_owner import (
    LookupKeypairOwnerByAccessKeyAction,
)
from ai.backend.manager.services.user.actions.update_keypair_dotfile import (
    UpdateKeypairDotfileAction,
)
from ai.backend.manager.services.user.processors import UserProcessors

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class UserConfigHandler:
    """User config (dotfile) API handler with constructor-injected dependencies."""

    def __init__(self, *, auth: AuthProcessors, user: UserProcessors) -> None:
        self._auth = auth
        self._user = user

    async def _owner_access_key(self, ctx: UserContext, owner: str | None) -> AccessKey:
        scope = await self._auth.resolve_access_key_scope.wait_for_complete(
            ResolveAccessKeyScopeAction(
                requester_access_key=ctx.access_key,
                requester_role=ctx.user_role,
                requester_domain=ctx.user_domain,
                owner_access_key=owner,
            )
        )
        return AccessKey(scope.owner_access_key)

    async def _owner(self, access_key: AccessKey) -> UserID:
        result = await self._user.lookup_keypair_owner.run(
            LookupKeypairOwnerByAccessKeyAction(access_key=access_key)
        )
        return UserID(result.entity_id())

    async def create(
        self,
        body: BodyParam[CreateUserDotfileRequest],
        ctx: UserContext,
    ) -> APIResponse:
        params = body.parsed
        access_key = await self._owner_access_key(ctx, params.owner_access_key)
        log.info("USERCONFIG.CREATE(ak:{})", access_key)
        await self._user.create_dotfile.run(
            CreateKeypairDotfileAction(
                user_id=await self._owner(access_key),
                access_key=access_key,
                entry=DotfileEntry(path=params.path, perm=params.permission, data=params.data),
            )
        )
        return APIResponse.build(HTTPStatus.OK, CreateDotfileResponse())

    async def list_or_get(
        self,
        query: QueryParam[GetUserDotfileRequest],
        ctx: UserContext,
    ) -> APIResponse:
        params = query.parsed
        access_key = await self._owner_access_key(ctx, params.owner_access_key)
        log.info("USERCONFIG.LIST_OR_GET(ak:{})", access_key)
        keypair = await self._user.admin_get_keypair.run(
            AdminGetKeypairAction(user_id=await self._owner(access_key), access_key=access_key)
        )
        entries = DotfileEntries.unpack(keypair.keypair.dotfiles)
        if params.path:
            entry = entries.get(params.path)
            return APIResponse.build(
                HTTPStatus.OK,
                GetDotfileResponse(path=entry.path, perm=entry.perm, data=entry.data),
            )
        items = [
            DotfileListItem(path=e.path, permission=e.perm, data=e.data) for e in entries.entries
        ]
        return APIResponse.build(HTTPStatus.OK, ListDotfilesResponse(root=items))

    async def update(
        self,
        body: BodyParam[UpdateUserDotfileRequest],
        ctx: UserContext,
    ) -> APIResponse:
        params = body.parsed
        access_key = await self._owner_access_key(ctx, params.owner_access_key)
        log.info("USERCONFIG.UPDATE(ak:{})", access_key)
        await self._user.update_dotfile.run(
            UpdateKeypairDotfileAction(
                user_id=await self._owner(access_key),
                access_key=access_key,
                entry=DotfileEntry(path=params.path, perm=params.permission, data=params.data),
            )
        )
        return APIResponse.build(HTTPStatus.OK, UpdateDotfileResponse())

    async def delete(
        self,
        query: QueryParam[DeleteUserDotfileRequest],
        ctx: UserContext,
    ) -> APIResponse:
        params = query.parsed
        access_key = await self._owner_access_key(ctx, params.owner_access_key)
        log.info("USERCONFIG.DELETE(ak:{})", access_key)
        await self._user.delete_dotfile.run(
            DeleteKeypairDotfileAction(
                user_id=await self._owner(access_key),
                access_key=access_key,
                path=params.path,
            )
        )
        return APIResponse.build(HTTPStatus.OK, DeleteDotfileResponse(success=True))

    async def update_bootstrap_script(
        self,
        body: BodyParam[UpdateBootstrapScriptRequest],
        ctx: UserContext,
    ) -> APIResponse:
        access_key = AccessKey(ctx.access_key)
        log.info("USERCONFIG.UPDATE_BOOTSTRAP_SCRIPT(ak:{})", access_key)
        await self._user.update_bootstrap_script.run(
            UpdateBootstrapScriptAction(
                user_id=await self._owner(access_key),
                access_key=access_key,
                script=body.parsed.script,
            )
        )
        return APIResponse.build(HTTPStatus.OK, UpdateBootstrapScriptResponse())

    async def get_bootstrap_script(
        self,
        ctx: UserContext,
    ) -> APIResponse:
        access_key = AccessKey(ctx.access_key)
        log.info("USERCONFIG.GET_BOOTSTRAP_SCRIPT(ak:{})", access_key)
        result = await self._user.get_bootstrap_script.run(
            GetBootstrapScriptAction(user_id=await self._owner(access_key), access_key=access_key)
        )
        return APIResponse.build(HTTPStatus.OK, GetBootstrapScriptResponse(root=result.script))
