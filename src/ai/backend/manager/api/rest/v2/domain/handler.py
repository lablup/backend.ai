"""REST v2 handler for the domain resource."""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from ai.backend.common.api_handlers import APIResponse, BodyParam, PathParam
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.domain.request import (
    AdminSearchDomainsInput,
    CreateDomainInput,
    DeleteDomainInput,
    PurgeDomainInput,
    UpdateDomainInput,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.api.rest.v2.path_params import DomainNamePathParam
from ai.backend.manager.data.domain.types import UserInfo
from ai.backend.manager.dto.context import UserContext

if TYPE_CHECKING:
    from ai.backend.manager.api.adapters.domain import DomainAdapter

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class V2DomainHandler:
    """REST v2 handler for domain operations."""

    def __init__(self, *, adapter: DomainAdapter) -> None:
        self._adapter = adapter

    @staticmethod
    def _build_user_info(ctx: UserContext) -> UserInfo:
        return UserInfo(
            id=ctx.user_uuid,
            role=UserRole(ctx.user_role),
            domain_name=ctx.user_domain,
        )

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
        result = await self._adapter.admin_search(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def admin_create(
        self,
        body: BodyParam[CreateDomainInput],
        ctx: UserContext,
    ) -> APIResponse:
        """Create a new domain (superadmin only)."""
        result = await self._adapter.admin_create(body.parsed, self._build_user_info(ctx))
        return APIResponse.build(status_code=HTTPStatus.CREATED, response_model=result)

    async def admin_update(
        self,
        path: PathParam[DomainNamePathParam],
        body: BodyParam[UpdateDomainInput],
        ctx: UserContext,
    ) -> APIResponse:
        """Update a domain (superadmin only)."""
        result = await self._adapter.admin_update(
            path.parsed.domain_name, body.parsed, self._build_user_info(ctx)
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def admin_delete(
        self,
        body: BodyParam[DeleteDomainInput],
        ctx: UserContext,
    ) -> APIResponse:
        """Soft-delete a domain (superadmin only)."""
        result = await self._adapter.admin_delete(body.parsed, self._build_user_info(ctx))
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def admin_purge(
        self,
        body: BodyParam[PurgeDomainInput],
        ctx: UserContext,
    ) -> APIResponse:
        """Permanently purge a domain (superadmin only)."""
        result = await self._adapter.admin_purge(body.parsed, self._build_user_info(ctx))
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)
