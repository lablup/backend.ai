"""Fetcher functions for resource slot GQL queries.

These functions are shared between root queries (resolver.py) and node connection
resolvers (AgentV2GQL.resource_slots, KernelV2GQL.resource_allocations) to avoid
duplicating query logic.
"""

from __future__ import annotations

import strawberry
from strawberry import Info

from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.errors.resource_slot import ResourceSlotTypeNotFound
from ai.backend.manager.services.resource_slot.actions.all_slot_types import AllSlotTypesAction
from ai.backend.manager.services.resource_slot.actions.get_agent_resources import (
    GetAgentResourcesAction,
)
from ai.backend.manager.services.resource_slot.actions.get_kernel_allocations import (
    GetKernelAllocationsAction,
)
from ai.backend.manager.services.resource_slot.actions.get_resource_slot_type import (
    GetResourceSlotTypeAction,
)

from .types import (
    AgentResourceConnectionGQL,
    AgentResourceSlotEdgeGQL,
    AgentResourceSlotGQL,
    KernelResourceAllocationEdgeGQL,
    KernelResourceAllocationGQL,
    ResourceAllocationConnectionGQL,
    ResourceSlotTypeConnectionGQL,
    ResourceSlotTypeEdgeGQL,
    ResourceSlotTypeGQL,
)


async def fetch_resource_slot_types(
    info: Info[StrawberryGQLContext],
) -> ResourceSlotTypeConnectionGQL:
    """Fetch all registered resource slot types (shared between root query and node resolver)."""
    action_result = await info.context.processors.resource_slot.all_slot_types.wait_for_complete(
        AllSlotTypesAction()
    )

    edges = []
    for data in action_result.items:
        node = ResourceSlotTypeGQL.from_data(data)
        cursor = encode_cursor(data.slot_name)
        edges.append(ResourceSlotTypeEdgeGQL(node=node, cursor=cursor))

    page_info = strawberry.relay.PageInfo(
        has_next_page=False,
        has_previous_page=False,
        start_cursor=edges[0].cursor if edges else None,
        end_cursor=edges[-1].cursor if edges else None,
    )

    return ResourceSlotTypeConnectionGQL(
        count=len(edges),
        edges=edges,
        page_info=page_info,
    )


async def fetch_resource_slot_type(
    info: Info[StrawberryGQLContext],
    slot_name: str,
) -> ResourceSlotTypeGQL | None:
    """Fetch a single resource slot type by slot_name (used by Node resolution and root query)."""
    try:
        action_result = (
            await info.context.processors.resource_slot.get_resource_slot_type.wait_for_complete(
                GetResourceSlotTypeAction(slot_name=slot_name)
            )
        )
    except ResourceSlotTypeNotFound:
        return None
    return ResourceSlotTypeGQL.from_data(action_result.item)


async def fetch_agent_resources(
    info: Info[StrawberryGQLContext],
    agent_id: str,
) -> AgentResourceConnectionGQL:
    """Fetch all per-slot resource entries for a given agent (shared for AgentV2GQL connection)."""
    action_result = (
        await info.context.processors.resource_slot.get_agent_resources.wait_for_complete(
            GetAgentResourcesAction(agent_id=agent_id)
        )
    )

    edges = []
    for data in action_result.items:
        node = AgentResourceSlotGQL.from_data(data)
        cursor = encode_cursor(f"{data.agent_id}:{data.slot_name}")
        edges.append(AgentResourceSlotEdgeGQL(node=node, cursor=cursor))

    page_info = strawberry.relay.PageInfo(
        has_next_page=False,
        has_previous_page=False,
        start_cursor=edges[0].cursor if edges else None,
        end_cursor=edges[-1].cursor if edges else None,
    )

    return AgentResourceConnectionGQL(
        count=len(edges),
        edges=edges,
        page_info=page_info,
    )


async def fetch_agent_resource_slot(
    info: Info[StrawberryGQLContext],
    agent_id: str,
    slot_name: str,
) -> AgentResourceSlotGQL | None:
    """Fetch a single per-slot resource entry for an agent (used by Node resolution)."""
    action_result = (
        await info.context.processors.resource_slot.get_agent_resources.wait_for_complete(
            GetAgentResourcesAction(agent_id=agent_id)
        )
    )
    for data in action_result.items:
        if data.slot_name == slot_name:
            return AgentResourceSlotGQL.from_data(data)
    return None


async def fetch_kernel_allocations(
    info: Info[StrawberryGQLContext],
    kernel_id: str,
) -> ResourceAllocationConnectionGQL:
    """Fetch all per-slot allocation entries for a kernel (shared for KernelV2GQL connection)."""
    import uuid

    action_result = (
        await info.context.processors.resource_slot.get_kernel_allocations.wait_for_complete(
            GetKernelAllocationsAction(kernel_id=uuid.UUID(kernel_id))
        )
    )

    edges = []
    for data in action_result.items:
        node = KernelResourceAllocationGQL.from_data(data)
        cursor = encode_cursor(f"{data.kernel_id}:{data.slot_name}")
        edges.append(KernelResourceAllocationEdgeGQL(node=node, cursor=cursor))

    page_info = strawberry.relay.PageInfo(
        has_next_page=False,
        has_previous_page=False,
        start_cursor=edges[0].cursor if edges else None,
        end_cursor=edges[-1].cursor if edges else None,
    )

    return ResourceAllocationConnectionGQL(
        count=len(edges),
        edges=edges,
        page_info=page_info,
    )


async def fetch_kernel_resource_allocation(
    info: Info[StrawberryGQLContext],
    kernel_id_str: str,
    slot_name: str,
) -> KernelResourceAllocationGQL | None:
    """Fetch a single per-slot allocation for a kernel (used by Node resolution)."""
    import uuid

    action_result = (
        await info.context.processors.resource_slot.get_kernel_allocations.wait_for_complete(
            GetKernelAllocationsAction(kernel_id=uuid.UUID(kernel_id_str))
        )
    )
    for data in action_result.items:
        if data.slot_name == slot_name:
            return KernelResourceAllocationGQL.from_data(data)
    return None
