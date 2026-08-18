"""Group config handler class using constructor dependency injection.

A project's dotfiles are a column of the project row, so every operation here is a
read or an update of that project.
"""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import Final
from uuid import UUID

from ai.backend.common.api_handlers import APIResponse, BodyParam, QueryParam
from ai.backend.common.data.entity.domain import DomainName
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.dto.manager.config.request import (
    CreateGroupDotfileRequest,
    DeleteGroupDotfileRequest,
    GetGroupDotfileRequest,
    UpdateGroupDotfileRequest,
)
from ai.backend.common.dto.manager.config.response import (
    CreateDotfileResponse,
    DeleteDotfileResponse,
    DotfileListItem,
    GetDotfileResponse,
    ListDotfilesResponse,
    UpdateDotfileResponse,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.dotfile.types import DotfileEntries, DotfileEntry
from ai.backend.manager.dto.context import UserContext
from ai.backend.manager.services.group.actions.create_project_dotfile import (
    CreateProjectDotfileAction,
)
from ai.backend.manager.services.group.actions.delete_project_dotfile import (
    DeleteProjectDotfileAction,
)
from ai.backend.manager.services.group.actions.lookup import LookupProjectAction
from ai.backend.manager.services.group.actions.search_projects import GetProjectAction
from ai.backend.manager.services.group.actions.update_project_dotfile import (
    UpdateProjectDotfileAction,
)
from ai.backend.manager.services.group.processors import GroupProcessors

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class GroupConfigHandler:
    """Group config (dotfile) API handler with constructor-injected dependencies."""

    def __init__(self, *, group: GroupProcessors) -> None:
        self._group = group

    async def _resolve(self, group: UUID | str, domain: str | None, ctx: UserContext) -> ProjectID:
        if isinstance(group, UUID):
            return ProjectID(group)
        result = await self._group.lookup.run(
            LookupProjectAction(
                domain_name=DomainName(domain or ctx.user_domain), project_name=group
            )
        )
        return result.data.entity_id()

    async def create(
        self,
        body: BodyParam[CreateGroupDotfileRequest],
        ctx: UserContext,
    ) -> APIResponse:
        params = body.parsed
        log.info("GROUPCONFIG.CREATE(group:{})", params.group)
        project_id = await self._resolve(params.group, params.domain, ctx)
        await self._group.create_dotfile.run(
            CreateProjectDotfileAction(
                project_id=project_id,
                entry=DotfileEntry(path=params.path, perm=params.permission, data=params.data),
            )
        )
        return APIResponse.build(HTTPStatus.OK, CreateDotfileResponse())

    async def list_or_get(
        self,
        query: QueryParam[GetGroupDotfileRequest],
        ctx: UserContext,
    ) -> APIResponse:
        params = query.parsed
        log.info("GROUPCONFIG.LIST_OR_GET(group:{})", params.group)
        project_id = await self._resolve(params.group, params.domain, ctx)
        project = await self._group.get_project.run(GetProjectAction(project_id=project_id))
        entries = DotfileEntries.unpack(project.data.dotfiles)
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
        body: BodyParam[UpdateGroupDotfileRequest],
        ctx: UserContext,
    ) -> APIResponse:
        params = body.parsed
        log.info("GROUPCONFIG.UPDATE(group:{})", params.group)
        project_id = await self._resolve(params.group, params.domain, ctx)
        await self._group.update_dotfile.run(
            UpdateProjectDotfileAction(
                project_id=project_id,
                entry=DotfileEntry(path=params.path, perm=params.permission, data=params.data),
            )
        )
        return APIResponse.build(HTTPStatus.OK, UpdateDotfileResponse())

    async def delete(
        self,
        query: QueryParam[DeleteGroupDotfileRequest],
        ctx: UserContext,
    ) -> APIResponse:
        params = query.parsed
        log.info("GROUPCONFIG.DELETE(group:{})", params.group)
        project_id = await self._resolve(params.group, params.domain, ctx)
        await self._group.delete_dotfile.run(
            DeleteProjectDotfileAction(project_id=project_id, path=params.path)
        )
        return APIResponse.build(HTTPStatus.OK, DeleteDotfileResponse(success=True))
