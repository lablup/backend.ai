from __future__ import annotations

from ai.backend.manager.data.resource_slot.types import (
    AgentResourceData,
    ResourceAllocationData,
    ResourceOccupancy,
)
from ai.backend.manager.repositories.resource_slot.repository import ResourceSlotRepository

from .actions.get_agent_resource_by_slot import (
    GetAgentResourceBySlotAction,
    GetAgentResourceBySlotResult,
)
from .actions.get_domain_resource_overview import (
    GetDomainResourceOverviewAction,
    GetDomainResourceOverviewResult,
)
from .actions.get_kernel_allocation_by_slot import (
    GetKernelAllocationBySlotAction,
    GetKernelAllocationBySlotResult,
)
from .actions.get_project_resource_overview import (
    GetProjectResourceOverviewAction,
    GetProjectResourceOverviewResult,
)
from .actions.search_agent_resources import (
    GlobalSearchAgentResourcesAction,
    GlobalSearchAgentResourcesResult,
)
from .actions.search_resource_allocations import (
    GlobalSearchResourceAllocationsAction,
    GlobalSearchResourceAllocationsResult,
)


class ResourceSlotService:
    _repository: ResourceSlotRepository

    def __init__(self, repository: ResourceSlotRepository) -> None:
        self._repository = repository

    async def get_agent_resource_by_slot(
        self, action: GetAgentResourceBySlotAction
    ) -> GetAgentResourceBySlotResult:
        row = await self._repository.get_agent_resource_by_slot(action.agent_id, action.slot_name)
        return GetAgentResourceBySlotResult(
            item=AgentResourceData(
                agent_id=row.agent_id,
                slot_name=row.slot_name,
                capacity=row.capacity,
                reserved=row.reserved,
                used=row.used,
            )
        )

    async def search_agent_resources(
        self, action: GlobalSearchAgentResourcesAction
    ) -> GlobalSearchAgentResourcesResult:
        result = await self._repository.search_agent_resources(action.querier)
        return GlobalSearchAgentResourcesResult(
            items=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def get_kernel_allocation_by_slot(
        self, action: GetKernelAllocationBySlotAction
    ) -> GetKernelAllocationBySlotResult:
        row = await self._repository.get_kernel_allocation_by_slot(
            action.kernel_id, action.slot_name
        )
        return GetKernelAllocationBySlotResult(
            item=ResourceAllocationData(
                kernel_id=row.kernel_id,
                slot_name=row.slot_name,
                requested=row.requested,
                used=row.used,
            )
        )

    async def search_resource_allocations(
        self, action: GlobalSearchResourceAllocationsAction
    ) -> GlobalSearchResourceAllocationsResult:
        result = await self._repository.search_resource_allocations(action.querier)
        return GlobalSearchResourceAllocationsResult(
            items=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def get_domain_resource_overview(
        self, action: GetDomainResourceOverviewAction
    ) -> GetDomainResourceOverviewResult:
        occupancy: ResourceOccupancy = await self._repository.get_domain_resource_overview(
            action.domain_name
        )
        return GetDomainResourceOverviewResult(item=occupancy)

    async def get_project_resource_overview(
        self, action: GetProjectResourceOverviewAction
    ) -> GetProjectResourceOverviewResult:
        occupancy: ResourceOccupancy = await self._repository.get_project_resource_overview(
            action.project_id
        )
        return GetProjectResourceOverviewResult(item=occupancy)
