"""V2 SDK client for the resource slot domain."""

from __future__ import annotations

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.v2.resource_slot.request import (
    AdminSearchAgentResourcesInput,
    AdminSearchResourceAllocationsInput,
    AdminSearchResourceSlotTypesInput,
)
from ai.backend.common.dto.manager.v2.resource_slot.response import (
    AdminSearchAgentResourcesPayload,
    AdminSearchResourceAllocationsPayload,
    AdminSearchResourceSlotTypesPayload,
)

_PATH = "/v2/resource-slots"


class V2ResourceSlotClient(BaseDomainClient):
    """SDK client for resource slot operations."""

    async def search_slot_types(
        self, request: AdminSearchResourceSlotTypesInput
    ) -> AdminSearchResourceSlotTypesPayload:
        """Search resource slot types with filters, orders, and pagination."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/slot-types/search",
            request=request,
            response_model=AdminSearchResourceSlotTypesPayload,
        )

    async def search_agent_resources(
        self, request: AdminSearchAgentResourcesInput
    ) -> AdminSearchAgentResourcesPayload:
        """Search agent resources with filters, orders, and pagination."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/agent-resources/search",
            request=request,
            response_model=AdminSearchAgentResourcesPayload,
        )

    async def search_allocations(
        self, request: AdminSearchResourceAllocationsInput
    ) -> AdminSearchResourceAllocationsPayload:
        """Search resource allocations with filters, orders, and pagination."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/allocations/search",
            request=request,
            response_model=AdminSearchResourceAllocationsPayload,
        )
