"""REST v2 handler for the domain resource."""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from ai.backend.common.api_handlers import APIResponse, BodyParam, PathParam
from ai.backend.common.dto.manager.v2.domain.request import AdminSearchDomainsInput
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.api.rest.v2.path_params import DomainNamePathParam

if TYPE_CHECKING:
    from ai.backend.manager.api.adapters.domain import DomainAdapter

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


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
        result = await self._adapter.admin_search(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)
