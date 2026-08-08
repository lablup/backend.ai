from __future__ import annotations

from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.registry import ProcessorGroup
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.actions.v2.global_scope.processor import GlobalActionProcessor
from ai.backend.manager.actions.v2.ops.result import CreatedEntityOpsResult, EntityOpsResult
from ai.backend.manager.actions.validators import ActionValidators
from ai.backend.manager.data.resource_slot.types import ResourceSlotTypeData
from ai.backend.manager.services.resource_slot.actions.create import CreateResourceSlotTypeAction
from ai.backend.manager.services.resource_slot.actions.purge import PurgeResourceSlotTypeAction
from ai.backend.manager.services.resource_slot.actions.update import UpdateResourceSlotTypeAction

from .actions import (
    GetAgentResourceBySlotAction,
    GetAgentResourceBySlotResult,
    GetAgentResourcesAction,
    GetAgentResourcesResult,
    GetDomainResourceOverviewAction,
    GetDomainResourceOverviewResult,
    GetKernelAllocationBySlotAction,
    GetKernelAllocationBySlotResult,
    GetKernelAllocationsAction,
    GetKernelAllocationsResult,
    GetProjectResourceOverviewAction,
    GetProjectResourceOverviewResult,
    GetResourceSlotTypeAction,
    GetResourceSlotTypeResult,
    SearchAgentResourcesAction,
    SearchAgentResourcesResult,
    SearchResourceAllocationsAction,
    SearchResourceAllocationsResult,
    SearchResourceSlotTypesAction,
    SearchResourceSlotTypesResult,
)
from .service import ResourceSlotService


class ResourceSlotProcessors(AbstractProcessorPackage):
    get_agent_resource_by_slot: ActionProcessor[
        GetAgentResourceBySlotAction, GetAgentResourceBySlotResult
    ]
    get_agent_resources: ActionProcessor[GetAgentResourcesAction, GetAgentResourcesResult]
    get_kernel_allocation_by_slot: ActionProcessor[
        GetKernelAllocationBySlotAction, GetKernelAllocationBySlotResult
    ]
    search_agent_resources: ActionProcessor[SearchAgentResourcesAction, SearchAgentResourcesResult]
    get_kernel_allocations: ActionProcessor[GetKernelAllocationsAction, GetKernelAllocationsResult]
    search_resource_allocations: ActionProcessor[
        SearchResourceAllocationsAction, SearchResourceAllocationsResult
    ]
    get_resource_slot_type: ActionProcessor[GetResourceSlotTypeAction, GetResourceSlotTypeResult]
    search_resource_slot_types: ActionProcessor[
        SearchResourceSlotTypesAction, SearchResourceSlotTypesResult
    ]
    get_domain_resource_overview: ActionProcessor[
        GetDomainResourceOverviewAction, GetDomainResourceOverviewResult
    ]
    get_project_resource_overview: ActionProcessor[
        GetProjectResourceOverviewAction, GetProjectResourceOverviewResult
    ]
    create_resource_slot_type: GlobalActionProcessor[
        CreateResourceSlotTypeAction,
        CreatedEntityOpsResult[ResourceSlotTypeData],
    ]
    update_resource_slot_type: GlobalActionProcessor[
        UpdateResourceSlotTypeAction,
        EntityOpsResult[ResourceSlotTypeData],
    ]
    purge_resource_slot_type: GlobalActionProcessor[
        PurgeResourceSlotTypeAction,
        EntityOpsResult[ResourceSlotTypeData],
    ]

    def __init__(
        self,
        service: ResourceSlotService,
        action_monitors: list[ActionMonitor],
        validators: ActionValidators,
        group: ProcessorGroup[ResourceSlotTypeData],
    ) -> None:
        self.get_agent_resource_by_slot = ActionProcessor(
            service.get_agent_resource_by_slot, action_monitors
        )
        self.get_agent_resources = ActionProcessor(service.get_agent_resources, action_monitors)
        self.get_kernel_allocation_by_slot = ActionProcessor(
            service.get_kernel_allocation_by_slot, action_monitors
        )
        self.search_agent_resources = ActionProcessor(
            service.search_agent_resources, action_monitors
        )
        self.get_kernel_allocations = ActionProcessor(
            service.get_kernel_allocations, action_monitors
        )
        self.search_resource_allocations = ActionProcessor(
            service.search_resource_allocations, action_monitors
        )
        self.get_resource_slot_type = ActionProcessor(
            service.get_resource_slot_type, action_monitors
        )
        self.search_resource_slot_types = ActionProcessor(
            service.search_resource_slot_types, action_monitors
        )
        self.get_domain_resource_overview = ActionProcessor(
            service.get_domain_resource_overview, action_monitors
        )
        self.get_project_resource_overview = ActionProcessor(
            service.get_project_resource_overview, action_monitors
        )
        self.create_resource_slot_type = group.global_create_ops(CreateResourceSlotTypeAction)
        self.update_resource_slot_type = group.global_update_ops(UpdateResourceSlotTypeAction)
        self.purge_resource_slot_type = group.global_purge_ops(PurgeResourceSlotTypeAction)

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            GetAgentResourceBySlotAction.spec(),
            GetAgentResourcesAction.spec(),
            GetKernelAllocationBySlotAction.spec(),
            SearchAgentResourcesAction.spec(),
            GetKernelAllocationsAction.spec(),
            SearchResourceAllocationsAction.spec(),
            GetResourceSlotTypeAction.spec(),
            SearchResourceSlotTypesAction.spec(),
            GetDomainResourceOverviewAction.spec(),
            GetProjectResourceOverviewAction.spec(),
            CreateResourceSlotTypeAction.spec(),
            UpdateResourceSlotTypeAction.spec(),
            PurgeResourceSlotTypeAction.spec(),
        ]
