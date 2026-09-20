from __future__ import annotations

from ai.backend.manager.data.resource_slot.types import (
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


class ResourceSlotService:
    _repository: ResourceSlotRepository

    def __init__(self, repository: ResourceSlotRepository) -> None:
        self._repository = repository

    async def get_agent_resource_by_slot(
        self, action: GetAgentResourceBySlotAction
    ) -> GetAgentResourceBySlotResult:
        row = await self._repository.get_agent_resource_by_slot(action.agent_id, action.slot_name)
        return GetAgentResourceBySlotResult(item=row.to_data())

    async def get_kernel_allocation_by_slot(
        self, action: GetKernelAllocationBySlotAction
    ) -> GetKernelAllocationBySlotResult:
        row = await self._repository.get_kernel_allocation_by_slot(
            action.kernel_id, action.slot_name
        )
        return GetKernelAllocationBySlotResult(
            item=ResourceAllocationData(
                id=row.id,
                kernel_id=row.kernel_id,
                slot_name=row.slot_name,
                requested=row.requested,
                used=row.used,
            )
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
