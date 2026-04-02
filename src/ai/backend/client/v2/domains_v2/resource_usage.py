"""V2 SDK client for the resource usage domain."""

from __future__ import annotations

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.v2.resource_usage.request import (
    AdminSearchDomainUsageBucketsInput,
    AdminSearchProjectUsageBucketsInput,
    AdminSearchUserUsageBucketsInput,
)
from ai.backend.common.dto.manager.v2.resource_usage.response import (
    AdminSearchDomainUsageBucketsPayload,
    AdminSearchProjectUsageBucketsPayload,
    AdminSearchUserUsageBucketsPayload,
)

_PATH = "/v2/resource-usage"


class V2ResourceUsageClient(BaseDomainClient):
    """SDK client for resource usage operations."""

    async def search_domain_usage(
        self, request: AdminSearchDomainUsageBucketsInput
    ) -> AdminSearchDomainUsageBucketsPayload:
        """Search domain usage buckets without scope restriction."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/domains/search",
            request=request,
            response_model=AdminSearchDomainUsageBucketsPayload,
        )

    async def search_project_usage(
        self, request: AdminSearchProjectUsageBucketsInput
    ) -> AdminSearchProjectUsageBucketsPayload:
        """Search project usage buckets without scope restriction."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/projects/search",
            request=request,
            response_model=AdminSearchProjectUsageBucketsPayload,
        )

    async def search_user_usage(
        self, request: AdminSearchUserUsageBucketsInput
    ) -> AdminSearchUserUsageBucketsPayload:
        """Search user usage buckets without scope restriction."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/users/search",
            request=request,
            response_model=AdminSearchUserUsageBucketsPayload,
        )
