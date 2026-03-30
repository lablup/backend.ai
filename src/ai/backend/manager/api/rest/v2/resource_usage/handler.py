"""REST v2 handler for the resource usage domain."""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from ai.backend.common.api_handlers import APIResponse, BodyParam
from ai.backend.common.dto.manager.v2.resource_usage.request import (
    AdminSearchDomainUsageBucketsInput,
    AdminSearchProjectUsageBucketsInput,
    AdminSearchUserUsageBucketsInput,
)
from ai.backend.logging import BraceStyleAdapter

if TYPE_CHECKING:
    from ai.backend.manager.api.adapters.resource_usage import ResourceUsageAdapter

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class V2ResourceUsageHandler:
    """REST v2 handler for resource usage operations."""

    def __init__(self, *, adapter: ResourceUsageAdapter) -> None:
        self._adapter = adapter

    async def admin_search_domain(
        self,
        body: BodyParam[AdminSearchDomainUsageBucketsInput],
    ) -> APIResponse:
        """Search domain usage buckets without scope restriction."""
        result = await self._adapter.admin_search_domain(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def admin_search_project(
        self,
        body: BodyParam[AdminSearchProjectUsageBucketsInput],
    ) -> APIResponse:
        """Search project usage buckets without scope restriction."""
        result = await self._adapter.admin_search_project(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def admin_search_user(
        self,
        body: BodyParam[AdminSearchUserUsageBucketsInput],
    ) -> APIResponse:
        """Search user usage buckets without scope restriction."""
        result = await self._adapter.admin_search_user(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)
