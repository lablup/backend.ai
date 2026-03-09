from __future__ import annotations

from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.actions.validators import ActionValidators

from .actions import (
    GetAgentResourcesAction,
    GetAgentResourcesResult,
    GetDomainResourceOverviewAction,
    GetDomainResourceOverviewResult,
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
    get_agent_resources: ActionProcessor[GetAgentResourcesAction, GetAgentResourcesResult]
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

    def __init__(
        self,
        service: ResourceSlotService,
        action_monitors: list[ActionMonitor],
        validators: ActionValidators,
    ) -> None:
        self.get_agent_resources = ActionProcessor(service.get_agent_resources, action_monitors)
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

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            GetAgentResourcesAction.spec(),
            SearchAgentResourcesAction.spec(),
            GetKernelAllocationsAction.spec(),
            SearchResourceAllocationsAction.spec(),
            GetResourceSlotTypeAction.spec(),
            SearchResourceSlotTypesAction.spec(),
            GetDomainResourceOverviewAction.spec(),
            GetProjectResourceOverviewAction.spec(),
        ]
