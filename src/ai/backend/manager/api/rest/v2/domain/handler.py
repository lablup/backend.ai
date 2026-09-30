"""REST v2 handler for the domain resource."""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from ai.backend.common.api_handlers import APIResponse, BodyParam, PathParam
from ai.backend.common.dto.manager.v2.domain.request import (
    AdminSearchDomainsInput,
    CreateDomainInput,
    DeleteDomainInput,
    PurgeDomainInput,
    RestoreDomainInput,
    ScopedSearchDomainsInput,
    UpdateDomainInput,
)
from ai.backend.logging.structured import StructuredLogger
from ai.backend.manager.api.rest.v2.path_params import DomainNamePathParam
from ai.backend.manager.dto.context import UserContext

if TYPE_CHECKING:
    from ai.backend.manager.api.adapters.domain.adapter import DomainAdapter

log: Final = StructuredLogger(logging.getLogger(__spec__.name))


class V2DomainHandler:
    """REST v2 handler for domain operations."""

    def __init__(self, *, adapter: DomainAdapter) -> None:
        self._adapter = adapter

    async def get(
        self,
        path: PathParam[DomainNamePathParam],
    ) -> APIResponse:
        """Retrieve a single domain by name."""
        result = await self._adapter.get(path.parsed.domain_name)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def admin_search(
        self,
        body: BodyParam[AdminSearchDomainsInput],
    ) -> APIResponse:
        """Search domains with filters, orders, and pagination (superadmin only)."""
        result = await self._adapter.global_search(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def scoped_search(
        self,
        body: BodyParam[ScopedSearchDomainsInput],
    ) -> APIResponse:
        """Search the domains the named scopes reach, combined with OR."""
        result = await self._adapter.scoped_search(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def admin_create(
        self,
        body: BodyParam[CreateDomainInput],
        ctx: UserContext,
    ) -> APIResponse:
        """Create a new domain (superadmin only)."""
        result = await self._adapter.create(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.CREATED, response_model=result)

    async def admin_update(
        self,
        path: PathParam[DomainNamePathParam],
        body: BodyParam[UpdateDomainInput],
        ctx: UserContext,
    ) -> APIResponse:
        """Update a domain (superadmin only)."""
        result = await self._adapter.update(path.parsed.domain_name, body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def admin_delete(
        self,
        body: BodyParam[DeleteDomainInput],
        ctx: UserContext,
    ) -> APIResponse:
        """Soft-delete a domain (superadmin only)."""
        result = await self._adapter.delete(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def admin_restore(
        self,
        body: BodyParam[RestoreDomainInput],
        ctx: UserContext,
    ) -> APIResponse:
        """Restore a soft-deleted domain (superadmin only)."""
        result = await self._adapter.restore(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def admin_purge(
        self,
        body: BodyParam[PurgeDomainInput],
        ctx: UserContext,
    ) -> APIResponse:
        """Permanently purge a domain (superadmin only)."""
        result = await self._adapter.purge(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)
