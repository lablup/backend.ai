"""V2 REST SDK client for the service catalog domain."""

from __future__ import annotations

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.v2.service_catalog.request import (
    AdminSearchServiceCatalogsInput,
)
from ai.backend.common.dto.manager.v2.service_catalog.response import (
    AdminSearchServiceCatalogsPayload,
)

_PATH = "/v2/service-catalogs"


class V2ServiceCatalogClient(BaseDomainClient):
    """SDK client for the ``/v2/service-catalogs`` REST endpoints."""

    async def admin_search(
        self,
        request: AdminSearchServiceCatalogsInput,
    ) -> AdminSearchServiceCatalogsPayload:
        """Search service catalog entries with admin scope."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/search",
            request=request,
            response_model=AdminSearchServiceCatalogsPayload,
        )
