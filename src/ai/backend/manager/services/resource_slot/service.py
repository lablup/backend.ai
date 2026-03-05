from __future__ import annotations

from ai.backend.manager.data.resource_slot.types import (
    AgentResourceData,
    NumberFormatData,
    ResourceAllocationData,
    ResourceSlotTypeData,
)
from ai.backend.manager.repositories.resource_slot.repository import ResourceSlotRepository

from .actions.get_agent_resources import GetAgentResourcesAction, GetAgentResourcesResult
from .actions.get_kernel_allocations import GetKernelAllocationsAction, GetKernelAllocationsResult
from .actions.get_resource_slot_type import GetResourceSlotTypeAction, GetResourceSlotTypeResult
from .actions.search_agent_resources import SearchAgentResourcesAction, SearchAgentResourcesResult
from .actions.search_resource_allocations import (
    SearchResourceAllocationsAction,
    SearchResourceAllocationsResult,
)
from .actions.search_resource_slot_types import (
    SearchResourceSlotTypesAction,
    SearchResourceSlotTypesResult,
)


class ResourceSlotService:
    _repository: ResourceSlotRepository

    def __init__(self, repository: ResourceSlotRepository) -> None:
        self._repository = repository

    async def get_agent_resources(self, action: GetAgentResourcesAction) -> GetAgentResourcesResult:
        rows = await self._repository.get_agent_resources(action.agent_id)
        items = [
            AgentResourceData(
                agent_id=row.agent_id,
                slot_name=row.slot_name,
                capacity=row.capacity,
                used=row.used,
            )
            for row in rows
        ]
        return GetAgentResourcesResult(items=items)

    async def search_agent_resources(
        self, action: SearchAgentResourcesAction
    ) -> SearchAgentResourcesResult:
        result = await self._repository.search_agent_resources(action.querier)
        return SearchAgentResourcesResult(
            items=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def get_kernel_allocations(
        self, action: GetKernelAllocationsAction
    ) -> GetKernelAllocationsResult:
        rows = await self._repository.get_kernel_allocations(action.kernel_id)
        items = [
            ResourceAllocationData(
                kernel_id=row.kernel_id,
                slot_name=row.slot_name,
                requested=row.requested,
                used=row.used,
            )
            for row in rows
        ]
        return GetKernelAllocationsResult(items=items)

    async def search_resource_allocations(
        self, action: SearchResourceAllocationsAction
    ) -> SearchResourceAllocationsResult:
        result = await self._repository.search_resource_allocations(action.querier)
        return SearchResourceAllocationsResult(
            items=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def get_resource_slot_type(
        self, action: GetResourceSlotTypeAction
    ) -> GetResourceSlotTypeResult:
        row = await self._repository.get_slot_type(action.slot_name)
        item = ResourceSlotTypeData(
            slot_name=row.slot_name,
            slot_type=row.slot_type,
            display_name=row.display_name,
            description=row.description,
            display_unit=row.display_unit,
            display_icon=row.display_icon,
            number_format=NumberFormatData(
                binary=row.number_format.binary,
                round_length=row.number_format.round_length,
            ),
            rank=row.rank,
        )
        return GetResourceSlotTypeResult(item=item)

    async def search_resource_slot_types(
        self, action: SearchResourceSlotTypesAction
    ) -> SearchResourceSlotTypesResult:
        result = await self._repository.search_slot_types(action.querier)
        return SearchResourceSlotTypesResult(
            items=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )
