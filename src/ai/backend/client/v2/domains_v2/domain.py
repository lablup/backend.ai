"""V2 REST SDK client for the domain resource."""

from __future__ import annotations

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.v2.domain.request import (
    AdminSearchDomainsInput,
)
from ai.backend.common.dto.manager.v2.domain.response import (
    AdminSearchDomainsPayload,
    DomainNode,
)

_PATH = "/v2/domains"


class V2DomainClient(BaseDomainClient):
    """SDK client for ``/v2/domains`` endpoints."""

    async def admin_search(
        self,
        request: AdminSearchDomainsInput,
    ) -> AdminSearchDomainsPayload:
        """Search domains with filters, orders, and pagination (superadmin only)."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/search",
            request=request,
            response_model=AdminSearchDomainsPayload,
        )

    async def get(self, domain_name: str) -> DomainNode:
        """Retrieve a single domain by name."""
        return await self._client.typed_request(
            "GET",
            f"{_PATH}/{domain_name}",
            response_model=DomainNode,
        )
