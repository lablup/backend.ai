"""REST v2 handler for the resource slot domain."""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from ai.backend.common.api_handlers import APIResponse, BodyParam, PathParam
from ai.backend.common.data.entity.resource_slot import ResourceSlotTypeUUID
from ai.backend.common.dto.manager.v2.resource_slot.request import (
    AdminSearchAgentResourcesInput,
    AdminSearchResourceAllocationsInput,
    AdminSearchResourceSlotTypesInput,
    CreateResourceSlotTypeInput,
    PartialBulkPurgeResourceSlotTypesInput,
    ScopedSearchAgentResourcesInput,
    UpdateResourceSlotTypeInput,
)
from ai.backend.logging.structured import StructuredLogger
from ai.backend.manager.api.rest.v2.path_params import SlotNamePathParam, SlotTypeIdPathParam

if TYPE_CHECKING:
    from ai.backend.manager.api.adapters.resource_slot.adapter import ResourceSlotAdapter

log: Final = StructuredLogger(logging.getLogger(__spec__.name))


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

    async def admin_create_slot_type(
        self,
        body: BodyParam[CreateResourceSlotTypeInput],
    ) -> APIResponse:
        """Register a new resource slot type (superadmin only)."""
        result = await self._adapter.admin_create_slot_type(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.CREATED, response_model=result)

    async def admin_update_slot_type(
        self,
        path: PathParam[SlotNamePathParam],
        body: BodyParam[UpdateResourceSlotTypeInput],
    ) -> APIResponse:
        """Update a resource slot type by slot name (superadmin only)."""
        merged = body.parsed.model_copy(update={"slot_name": path.parsed.slot_name})
        result = await self._adapter.admin_update_slot_type(merged)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def purge_slot_type(
        self,
        path: PathParam[SlotTypeIdPathParam],
    ) -> APIResponse:
        """Remove a resource slot type, refusing while anything still references it."""
        result = await self._adapter.purge_slot_type(ResourceSlotTypeUUID(path.parsed.slot_type_id))
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def partial_bulk_purge_slot_types(
        self,
        body: BodyParam[PartialBulkPurgeResourceSlotTypesInput],
    ) -> APIResponse:
        """Remove several resource slot types, answering for each one."""
        result = await self._adapter.partial_bulk_purge_slot_types(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def admin_purge_slot_type(
        self,
        path: PathParam[SlotNamePathParam],
    ) -> APIResponse:
        """Deprecated. Use `DELETE /v2/resource-slots/slot-types/{slot_type_id}`."""
        slot_type_id = await self._adapter.lookup_slot_type(path.parsed.slot_name)
        result = await self._adapter.purge_slot_type(slot_type_id)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def scoped_search_agent_resources(
        self,
        body: BodyParam[ScopedSearchAgentResourcesInput],
    ) -> APIResponse:
        """Read the slot rows the named agents carry, combined with OR."""
        result = await self._adapter.scoped_search_agent_resources(body.parsed)
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
