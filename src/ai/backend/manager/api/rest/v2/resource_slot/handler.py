"""REST v2 handler for the resource slot domain."""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from ai.backend.common.api_handlers import APIResponse, BodyParam
from ai.backend.common.dto.manager.v2.resource_slot.request import (
    AdminSearchAgentResourcesInput,
    AdminSearchResourceAllocationsInput,
    AdminSearchResourceSlotTypesInput,
)
from ai.backend.logging import BraceStyleAdapter

if TYPE_CHECKING:
    from ai.backend.manager.api.adapters.resource_slot import ResourceSlotAdapter

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class V2ResourceSlotHandler:
    """REST v2 handler for resource slot operations."""

    def __init__(self, *, adapter: ResourceSlotAdapter) -> None:
        self._adapter = adapter

    async def search_slot_types(
        self,
        body: BodyParam[AdminSearchResourceSlotTypesInput],
    ) -> APIResponse:
        """Search resource slot types with filters, orders, and pagination."""
        result = await self._adapter.search_slot_types(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def search_agent_resources(
        self,
        body: BodyParam[AdminSearchAgentResourcesInput],
    ) -> APIResponse:
        """Search agent resources with filters, orders, and pagination."""
        result = await self._adapter.search_agent_resources(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def search_allocations(
        self,
        body: BodyParam[AdminSearchResourceAllocationsInput],
    ) -> APIResponse:
        """Search resource allocations with filters, orders, and pagination."""
        result = await self._adapter.search_allocations(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)
