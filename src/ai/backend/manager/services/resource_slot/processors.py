from __future__ import annotations

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.registry import ProcessorGroup
from ai.backend.manager.actions.v2.global_scope.processor import (
    GlobalActionProcessor,
    PublicActionProcessor,
)
from ai.backend.manager.actions.v2.lookup.processor import PublicLookupActionProcessor
from ai.backend.manager.actions.v2.ops.result import (
    BatchOpsResult,
    CreatedEntityOpsResult,
    EntityOpsResult,
    LookupOpsResult,
)
from ai.backend.manager.actions.validators import ActionValidators
from ai.backend.manager.data.resource_slot.types import ResourceSlotTypeData
from ai.backend.manager.services.resource_slot.actions.create import CreateResourceSlotTypeAction
from ai.backend.manager.services.resource_slot.actions.get_agent_resource_by_slot import (
    GetAgentResourceBySlotAction,
    GetAgentResourceBySlotResult,
)
from ai.backend.manager.services.resource_slot.actions.get_domain_resource_overview import (
    GetDomainResourceOverviewAction,
    GetDomainResourceOverviewResult,
)
from ai.backend.manager.services.resource_slot.actions.get_kernel_allocation_by_slot import (
    GetKernelAllocationBySlotAction,
    GetKernelAllocationBySlotResult,
)
from ai.backend.manager.services.resource_slot.actions.get_project_resource_overview import (
    GetProjectResourceOverviewAction,
    GetProjectResourceOverviewResult,
)
from ai.backend.manager.services.resource_slot.actions.lookup import (
    LookupResourceSlotTypeAction,
)
from ai.backend.manager.services.resource_slot.actions.purge import PurgeResourceSlotTypeAction
from ai.backend.manager.services.resource_slot.actions.search_agent_resources import (
    SearchAgentResourcesAction,
    SearchAgentResourcesResult,
)
from ai.backend.manager.services.resource_slot.actions.search_resource_allocations import (
    SearchResourceAllocationsAction,
    SearchResourceAllocationsResult,
)
from ai.backend.manager.services.resource_slot.actions.search_resource_slot_types import (
    SearchResourceSlotTypesAction,
)
from ai.backend.manager.services.resource_slot.actions.update import UpdateResourceSlotTypeAction
from ai.backend.manager.services.resource_slot.service import ResourceSlotService


class ResourceSlotProcessors:
    get_agent_resource_by_slot: ActionProcessor[
        GetAgentResourceBySlotAction, GetAgentResourceBySlotResult
    ]
    get_kernel_allocation_by_slot: ActionProcessor[
        GetKernelAllocationBySlotAction, GetKernelAllocationBySlotResult
    ]
    search_agent_resources: ActionProcessor[SearchAgentResourcesAction, SearchAgentResourcesResult]
    search_resource_allocations: ActionProcessor[
        SearchResourceAllocationsAction, SearchResourceAllocationsResult
    ]
    public_lookup_resource_slot_type: PublicLookupActionProcessor[
        LookupResourceSlotTypeAction,
        LookupOpsResult[ResourceSlotTypeData],
    ]
    public_search_resource_slot_types: PublicActionProcessor[
        SearchResourceSlotTypesAction,
        BatchOpsResult[ResourceSlotTypeData],
    ]
    get_domain_resource_overview: ActionProcessor[
        GetDomainResourceOverviewAction, GetDomainResourceOverviewResult
    ]
    get_project_resource_overview: ActionProcessor[
        GetProjectResourceOverviewAction, GetProjectResourceOverviewResult
    ]
    global_create_resource_slot_type: GlobalActionProcessor[
        CreateResourceSlotTypeAction,
        CreatedEntityOpsResult[ResourceSlotTypeData],
    ]
    global_update_resource_slot_type: GlobalActionProcessor[
        UpdateResourceSlotTypeAction,
        EntityOpsResult[ResourceSlotTypeData],
    ]
    global_purge_resource_slot_type: GlobalActionProcessor[
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
        self.get_kernel_allocation_by_slot = ActionProcessor(
            service.get_kernel_allocation_by_slot, action_monitors
        )
        self.search_agent_resources = ActionProcessor(
            service.search_agent_resources, action_monitors
        )
        self.search_resource_allocations = ActionProcessor(
            service.search_resource_allocations, action_monitors
        )
        self.public_lookup_resource_slot_type = group.public_lookup_ops(
            LookupResourceSlotTypeAction
        )
        self.public_search_resource_slot_types = group.public_search_ops(
            SearchResourceSlotTypesAction
        )
        self.get_domain_resource_overview = ActionProcessor(
            service.get_domain_resource_overview, action_monitors
        )
        self.get_project_resource_overview = ActionProcessor(
            service.get_project_resource_overview, action_monitors
        )
        self.global_create_resource_slot_type = group.global_create_ops(
            CreateResourceSlotTypeAction
        )
        self.global_update_resource_slot_type = group.global_update_ops(
            UpdateResourceSlotTypeAction
        )
        self.global_purge_resource_slot_type = group.global_purge_ops(PurgeResourceSlotTypeAction)
