from __future__ import annotations

from ai.backend.manager.actions.registry.group import ProcessorGroup
from ai.backend.manager.actions.v2.global_scope.processor import (
    GlobalActionProcessor,
    PublicActionProcessor,
)
from ai.backend.manager.actions.v2.lookup.processor import LookupActionProcessor
from ai.backend.manager.actions.v2.ops.result import (
    BatchOpsResult,
    CreatedEntityOpsResult,
    EntityOpsResult,
    FieldOwnerLookupOpsResult,
    LookupOpsResult,
)
from ai.backend.manager.actions.v2.scope.processor import ScopeActionProcessor
from ai.backend.manager.actions.v2.single_entity.processor import SingleEntityActionProcessor
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
from ai.backend.manager.services.resource_slot.actions.lookup_kernel_owner import (
    LookupKernelOwnerAction,
)
from ai.backend.manager.services.resource_slot.actions.purge import PurgeResourceSlotTypeAction
from ai.backend.manager.services.resource_slot.actions.search_agent_resources import (
    GlobalSearchAgentResourcesAction,
    GlobalSearchAgentResourcesResult,
)
from ai.backend.manager.services.resource_slot.actions.search_resource_allocations import (
    GlobalSearchResourceAllocationsAction,
    GlobalSearchResourceAllocationsResult,
)
from ai.backend.manager.services.resource_slot.actions.search_resource_slot_types import (
    SearchResourceSlotTypesAction,
)
from ai.backend.manager.services.resource_slot.actions.update import UpdateResourceSlotTypeAction
from ai.backend.manager.services.resource_slot.service import ResourceSlotService


class ResourceSlotProcessors:
    lookup_kernel_owner: LookupActionProcessor[LookupKernelOwnerAction, FieldOwnerLookupOpsResult]
    get_agent_resource_by_slot: SingleEntityActionProcessor[
        GetAgentResourceBySlotAction, GetAgentResourceBySlotResult
    ]
    get_kernel_allocation_by_slot: SingleEntityActionProcessor[
        GetKernelAllocationBySlotAction, GetKernelAllocationBySlotResult
    ]
    search_agent_resources: GlobalActionProcessor[
        GlobalSearchAgentResourcesAction, GlobalSearchAgentResourcesResult
    ]
    search_resource_allocations: GlobalActionProcessor[
        GlobalSearchResourceAllocationsAction, GlobalSearchResourceAllocationsResult
    ]
    public_lookup_resource_slot_type: LookupActionProcessor[
        LookupResourceSlotTypeAction,
        LookupOpsResult[ResourceSlotTypeData],
    ]
    public_search_resource_slot_types: PublicActionProcessor[
        SearchResourceSlotTypesAction,
        BatchOpsResult[ResourceSlotTypeData],
    ]
    get_domain_resource_overview: ScopeActionProcessor[
        GetDomainResourceOverviewAction, GetDomainResourceOverviewResult
    ]
    get_project_resource_overview: ScopeActionProcessor[
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
    purge_resource_slot_type: SingleEntityActionProcessor[
        PurgeResourceSlotTypeAction,
        EntityOpsResult[ResourceSlotTypeData],
    ]

    def __init__(
        self,
        group: ProcessorGroup[ResourceSlotTypeData],
        service: ResourceSlotService,
    ) -> None:
        self.lookup_kernel_owner = group.key_owner_lookup_ops(LookupKernelOwnerAction)
        self.get_agent_resource_by_slot = group.single_entity(
            GetAgentResourceBySlotAction, service.get_agent_resource_by_slot
        )
        self.get_kernel_allocation_by_slot = group.single_entity(
            GetKernelAllocationBySlotAction, service.get_kernel_allocation_by_slot
        )
        self.search_agent_resources = group.global_scope(
            GlobalSearchAgentResourcesAction, service.search_agent_resources
        )
        self.search_resource_allocations = group.global_scope(
            GlobalSearchResourceAllocationsAction, service.search_resource_allocations
        )
        self.public_lookup_resource_slot_type = group.public_lookup_ops(
            LookupResourceSlotTypeAction
        )
        self.public_search_resource_slot_types = group.public_search_ops(
            SearchResourceSlotTypesAction
        )
        self.get_domain_resource_overview = group.scope(
            GetDomainResourceOverviewAction, service.get_domain_resource_overview
        )
        self.get_project_resource_overview = group.scope(
            GetProjectResourceOverviewAction, service.get_project_resource_overview
        )
        self.global_create_resource_slot_type = group.global_create_ops(
            CreateResourceSlotTypeAction
        )
        self.global_update_resource_slot_type = group.global_update_ops(
            UpdateResourceSlotTypeAction
        )
        self.purge_resource_slot_type = group.entity_purge_ops(PurgeResourceSlotTypeAction)
