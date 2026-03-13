"""Resource Slot Type handler class using constructor dependency injection."""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from ai.backend.common.api_handlers import APIResponse, BodyParam, PathParam
from ai.backend.common.dto.manager.resource_slot.request import (
    ResourceSlotTypePathParam,
    SearchResourceSlotTypesRequest,
)
from ai.backend.common.dto.manager.resource_slot.response import (
    GetResourceSlotTypeResponse,
    PaginationInfo,
    SearchResourceSlotTypesResponse,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.services.resource_slot.actions.get_resource_slot_type import (
    GetResourceSlotTypeAction,
)
from ai.backend.manager.services.resource_slot.actions.search_resource_slot_types import (
    SearchResourceSlotTypesAction,
)

from .adapter import ResourceSlotAdapter

if TYPE_CHECKING:
    from ai.backend.manager.services.resource_slot.processors import ResourceSlotProcessors

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ResourceSlotHandler:
    """Resource Slot Type API handler with constructor-injected dependencies."""

    def __init__(self, *, resource_slot: ResourceSlotProcessors) -> None:
        self._resource_slot = resource_slot
        self._adapter = ResourceSlotAdapter()

    async def search_resource_slot_types(
        self,
        body: BodyParam[SearchResourceSlotTypesRequest],
    ) -> APIResponse:
        """Search resource slot types with filters, orders, and pagination."""
        log.info("SEARCH_RESOURCE_SLOT_TYPES")

        querier = self._adapter.build_querier(body.parsed)

        action_result = await self._resource_slot.search_resource_slot_types.wait_for_complete(
            SearchResourceSlotTypesAction(querier=querier)
        )

        resp = SearchResourceSlotTypesResponse(
            items=[self._adapter.convert_to_dto(item) for item in action_result.items],
            pagination=PaginationInfo(
                total=action_result.total_count,
                offset=body.parsed.offset,
                limit=body.parsed.limit,
            ),
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    async def get_resource_slot_type(
        self,
        path: PathParam[ResourceSlotTypePathParam],
    ) -> APIResponse:
        """Get a single resource slot type by slot_name."""
        slot_name = path.parsed.slot_name
        log.info("GET_RESOURCE_SLOT_TYPE (slot_name:{})", slot_name)

        action_result = await self._resource_slot.get_resource_slot_type.wait_for_complete(
            GetResourceSlotTypeAction(slot_name=slot_name)
        )

        resp = GetResourceSlotTypeResponse(
            item=self._adapter.convert_to_dto(action_result.item),
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)
