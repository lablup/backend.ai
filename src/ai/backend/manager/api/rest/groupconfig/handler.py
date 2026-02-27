"""Group config handler class using constructor dependency injection.

All handlers use the new ApiHandler pattern: typed parameters
(``BodyParam``, ``QueryParam``, ``UserContext``, ``RequestCtx``) are
automatically extracted by ``_wrap_api_handler`` and responses are
returned as ``APIResponse`` objects.
"""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING, Final
from uuid import UUID

import sqlalchemy as sa

from ai.backend.common import msgpack
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
from ai.backend.common.dto.manager.config.types import MAXIMUM_DOTFILE_SIZE
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.dto.context import RequestCtx, UserContext
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.errors.common import GenericForbidden
from ai.backend.manager.errors.resource import ProjectNotFound
from ai.backend.manager.errors.storage import (
    DotfileAlreadyExists,
    DotfileCreationFailed,
    DotfileNotFound,
)
from ai.backend.manager.models.domain import verify_dotfile_name
from ai.backend.manager.models.group import (
    association_groups_users as agus,
)
from ai.backend.manager.models.group import (
    groups,
    query_group_domain,
    query_group_dotfiles,
)
from ai.backend.manager.services.processors import Processors

if TYPE_CHECKING:
    from ai.backend.manager.api.context import RootContext

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


async def _resolve_group_id_and_domain(
    conn: sa.ext.asyncio.engine.AsyncConnection,
    group_id_or_name: UUID | str,
    domain: str | None,
    *,
    user_domain: str | None = None,
) -> tuple[UUID | None, str | None]:
    """Resolve group identifier to (group_id, domain) pair.

    When *group_id_or_name* is a string that looks like a UUID, it is
    treated as a UUID (backward-compat with Trafaret's ``tx.UUID | t.String``).
    When it is a plain group name and *domain* is ``None``, *user_domain*
    is used as a fallback so that callers need not always supply a domain.
    """
    if isinstance(group_id_or_name, str):
        # Pydantic smart-union may parse a UUID-shaped string as str.
        try:
            group_id_or_name = UUID(group_id_or_name)
        except ValueError:
            pass
    if isinstance(group_id_or_name, UUID):
        resolved_domain = await query_group_domain(conn, group_id_or_name)
        return group_id_or_name, resolved_domain
    # group_id_or_name is a group name (non-UUID string)
    if domain is None:
        domain = user_domain
    if domain is None:
        raise InvalidAPIParameters("Missing parameter 'domain'")
    query = (
        sa.select(groups.c.id)
        .select_from(groups)
        .where(groups.c.domain_name == domain)
        .where(groups.c.name == group_id_or_name)
    )
    group_id = await conn.scalar(query)
    return group_id, domain


class GroupConfigHandler:
    """Group config (dotfile) API handler with constructor-injected dependencies."""

    def __init__(self, *, processors: Processors | None = None) -> None:
        self._processors = processors

    async def create(
        self,
        body: BodyParam[CreateGroupDotfileRequest],
        ctx: UserContext,
        req: RequestCtx,
    ) -> APIResponse:
        params = body.parsed
        log.info("GROUPCONFIG.CREATE(group:{})", params.group)
        root_ctx: RootContext = req.request.app["_root.context"]
        async with root_ctx.db.begin() as conn:
            group_id, domain = await _resolve_group_id_and_domain(
                conn,
                params.group,
                params.domain,
                user_domain=ctx.user_domain,
            )
            if group_id is None or domain is None:
                raise ProjectNotFound
            if not ctx.is_superadmin and ctx.user_domain != domain:
                raise GenericForbidden("Admins cannot create group dotfiles of other domains")

            dotfiles, leftover_space = await query_group_dotfiles(conn, group_id)
            if dotfiles is None:
                raise ProjectNotFound
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
            query = groups.update().values(dotfiles=dotfile_packed).where(groups.c.id == group_id)
            await conn.execute(query)
        return APIResponse.build(HTTPStatus.OK, CreateDotfileResponse())

    async def list_or_get(
        self,
        query: QueryParam[GetGroupDotfileRequest],
        ctx: UserContext,
        req: RequestCtx,
    ) -> APIResponse:
        params = query.parsed
        log.info("GROUPCONFIG.LIST_OR_GET(group:{})", params.group)
        root_ctx: RootContext = req.request.app["_root.context"]
        async with root_ctx.db.begin() as conn:
            group_id, domain = await _resolve_group_id_and_domain(
                conn,
                params.group,
                params.domain,
                user_domain=ctx.user_domain,
            )
            if group_id is None or domain is None:
                raise ProjectNotFound
            if not ctx.is_superadmin:
                if ctx.is_admin:
                    if ctx.user_domain != domain:
                        raise GenericForbidden(
                            "Domain admins cannot access group dotfiles of other domains"
                        )
                else:
                    q = (
                        sa.select(agus.c.group_id)
                        .select_from(agus)
                        .where(agus.c.user_id == ctx.user_uuid)
                    )
                    result = await conn.execute(q)
                    rows = result.fetchall()
                    if group_id not in map(lambda x: x.group_id, rows):
                        raise GenericForbidden("Users cannot access group dotfiles of other groups")

            if params.path:
                dotfiles, _ = await query_group_dotfiles(conn, group_id)
                if dotfiles is None:
                    raise ProjectNotFound
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
            dotfiles, _ = await query_group_dotfiles(conn, group_id)
            if dotfiles is None:
                raise ProjectNotFound
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
        body: BodyParam[UpdateGroupDotfileRequest],
        ctx: UserContext,
        req: RequestCtx,
    ) -> APIResponse:
        params = body.parsed
        log.info("GROUPCONFIG.UPDATE(group:{})", params.group)
        root_ctx: RootContext = req.request.app["_root.context"]
        async with root_ctx.db.begin() as conn:
            group_id, domain = await _resolve_group_id_and_domain(
                conn,
                params.group,
                params.domain,
                user_domain=ctx.user_domain,
            )
            if group_id is None or domain is None:
                raise ProjectNotFound
            if not ctx.is_superadmin and ctx.user_domain != domain:
                raise GenericForbidden("Admins cannot update group dotfiles of other domains")

            dotfiles, _ = await query_group_dotfiles(conn, group_id)
            if dotfiles is None:
                raise ProjectNotFound
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
            query = groups.update().values(dotfiles=dotfile_packed).where(groups.c.id == group_id)
            await conn.execute(query)
        return APIResponse.build(HTTPStatus.OK, UpdateDotfileResponse())

    async def delete(
        self,
        body: BodyParam[DeleteGroupDotfileRequest],
        ctx: UserContext,
        req: RequestCtx,
    ) -> APIResponse:
        params = body.parsed
        log.info("GROUPCONFIG.DELETE(group:{})", params.group)
        root_ctx: RootContext = req.request.app["_root.context"]
        async with root_ctx.db.begin() as conn:
            group_id, domain = await _resolve_group_id_and_domain(
                conn,
                params.group,
                params.domain,
                user_domain=ctx.user_domain,
            )
            if group_id is None or domain is None:
                raise ProjectNotFound
            if not ctx.is_superadmin and ctx.user_domain != domain:
                raise GenericForbidden("Admins cannot delete dotfiles of other domains")

            dotfiles, _ = await query_group_dotfiles(conn, group_id)
            if dotfiles is None:
                raise ProjectNotFound
            new_dotfiles = [x for x in dotfiles if x["path"] != params.path]
            if len(new_dotfiles) == len(dotfiles):
                raise DotfileNotFound
            dotfile_packed = msgpack.packb(new_dotfiles)
            query = groups.update().values(dotfiles=dotfile_packed).where(groups.c.id == group_id)
            await conn.execute(query)
        return APIResponse.build(HTTPStatus.OK, DeleteDotfileResponse(success=True))
