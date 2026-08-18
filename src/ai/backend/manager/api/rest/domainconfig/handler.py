"""Domain config handler class using constructor dependency injection.

A domain's dotfiles are a column of the domain row, so every operation here is a
read or an update of that domain.
"""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import Final

from ai.backend.common.api_handlers import APIResponse, BodyParam, QueryParam
from ai.backend.common.data.entity.domain import DomainName
from ai.backend.common.dto.manager.config.request import (
    CreateDomainDotfileRequest,
    DeleteDomainDotfileRequest,
    GetDomainDotfileRequest,
    UpdateDomainDotfileRequest,
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
from ai.backend.manager.services.domain.actions.create_domain_dotfile import (
    CreateDomainDotfileAction,
)
from ai.backend.manager.services.domain.actions.delete_domain_dotfile import (
    DeleteDomainDotfileAction,
)
from ai.backend.manager.services.domain.actions.lookup import LookupDomainAction
from ai.backend.manager.services.domain.actions.update_domain_dotfile import (
    UpdateDomainDotfileAction,
)
from ai.backend.manager.services.domain.processors import DomainProcessors

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class DomainConfigHandler:
    """Domain config (dotfile) API handler with constructor-injected dependencies."""

    def __init__(self, *, domain: DomainProcessors) -> None:
        self._domain = domain

    async def create(
        self,
        body: BodyParam[CreateDomainDotfileRequest],
        ctx: UserContext,
    ) -> APIResponse:
        params = body.parsed
        log.info("DOMAINCONFIG.CREATE(domain:{})", params.domain)
        target = await self._domain.lookup.run(LookupDomainAction(name=DomainName(params.domain)))
        await self._domain.create_dotfile.run(
            CreateDomainDotfileAction(
                domain_id=target.data.id,
                name=params.domain,
                entry=DotfileEntry(path=params.path, perm=params.permission, data=params.data),
            )
        )
        return APIResponse.build(HTTPStatus.OK, CreateDotfileResponse())

    async def list_or_get(
        self,
        query: QueryParam[GetDomainDotfileRequest],
        ctx: UserContext,
    ) -> APIResponse:
        params = query.parsed
        log.info("DOMAINCONFIG.LIST_OR_GET(domain:{})", params.domain)
        target = await self._domain.lookup.run(LookupDomainAction(name=DomainName(params.domain)))
        entries = DotfileEntries.unpack(target.data.dotfiles)
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
        body: BodyParam[UpdateDomainDotfileRequest],
        ctx: UserContext,
    ) -> APIResponse:
        params = body.parsed
        log.info("DOMAINCONFIG.UPDATE(domain:{})", params.domain)
        target = await self._domain.lookup.run(LookupDomainAction(name=DomainName(params.domain)))
        await self._domain.update_dotfile.run(
            UpdateDomainDotfileAction(
                domain_id=target.data.id,
                name=params.domain,
                entry=DotfileEntry(path=params.path, perm=params.permission, data=params.data),
            )
        )
        return APIResponse.build(HTTPStatus.OK, UpdateDotfileResponse())

    async def delete(
        self,
        query: QueryParam[DeleteDomainDotfileRequest],
        ctx: UserContext,
    ) -> APIResponse:
        params = query.parsed
        log.info("DOMAINCONFIG.DELETE(domain:{})", params.domain)
        target = await self._domain.lookup.run(LookupDomainAction(name=DomainName(params.domain)))
        await self._domain.delete_dotfile.run(
            DeleteDomainDotfileAction(
                domain_id=target.data.id, name=params.domain, path=params.path
            )
        )
        return APIResponse.build(HTTPStatus.OK, DeleteDotfileResponse(success=True))
