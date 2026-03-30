"""REST v2 handler for the service catalog domain."""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from ai.backend.common.api_handlers import APIResponse, BodyParam
from ai.backend.common.dto.manager.v2.service_catalog.request import (
    AdminSearchServiceCatalogsInput,
)
from ai.backend.logging import BraceStyleAdapter

if TYPE_CHECKING:
    from ai.backend.manager.api.adapters.service_catalog import ServiceCatalogAdapter

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class V2ServiceCatalogHandler:
    """REST v2 handler for service catalog operations."""

    def __init__(self, *, adapter: ServiceCatalogAdapter) -> None:
        self._adapter = adapter

    async def admin_search_service_catalogs(
        self,
        body: BodyParam[AdminSearchServiceCatalogsInput],
    ) -> APIResponse:
        """Search service catalog entries with admin scope."""
        result = await self._adapter.admin_search(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)
