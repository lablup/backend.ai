"""Fetcher functions for resource slot GQL queries.

These functions are shared between root queries (resolver.py) and node connection
resolvers (AgentV2GQL.resource_slots, KernelV2GQL.resource_allocations) to avoid
duplicating query logic.
"""

from __future__ import annotations

import uuid as _uuid
from functools import lru_cache

import strawberry
from strawberry import Info

from ai.backend.manager.api.gql.adapter import PaginationOptions, PaginationSpec
from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.data.resource_slot.types import (
    AgentResourceData,
    ResourceAllocationData,
    ResourceSlotTypeData,
)
from ai.backend.manager.models.resource_slot import ResourceSlotTypeRow
from ai.backend.manager.repositories.resource_slot.query import CursorConditions, QueryOrders
from ai.backend.manager.services.resource_slot.actions.get_agent_resources import (
    GetAgentResourcesAction,
)
from ai.backend.manager.services.resource_slot.actions.get_kernel_allocations import (
    GetKernelAllocationsAction,
)
from ai.backend.manager.services.resource_slot.actions.get_resource_slot_type import (
    GetResourceSlotTypeAction,
)
from ai.backend.manager.services.resource_slot.actions.search_resource_slot_types import (
    SearchResourceSlotTypesAction,
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
    ResourceSlotTypeFilterGQL,
    ResourceSlotTypeGQL,
    ResourceSlotTypeOrderByGQL,
)


@lru_cache(maxsize=1)
def _get_slot_type_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=QueryOrders.slot_name(ascending=True),
        backward_order=QueryOrders.slot_name(ascending=False),
        forward_condition_factory=CursorConditions.by_cursor_forward,
        backward_condition_factory=CursorConditions.by_cursor_backward,
        tiebreaker_order=ResourceSlotTypeRow.slot_name.asc(),
    )


async def fetch_resource_slot_types(
    info: Info[StrawberryGQLContext],
    filter: ResourceSlotTypeFilterGQL | None = None,
    order_by: list[ResourceSlotTypeOrderByGQL] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> ResourceSlotTypeConnectionGQL:
    """Fetch resource slot types with pagination and filtering."""
    querier = info.context.gql_adapter.build_querier(
        PaginationOptions(
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        ),
        pagination_spec=_get_slot_type_pagination_spec(),
        filter=filter,
        order_by=order_by,
    )

    action_result = (
        await info.context.processors.resource_slot.search_resource_slot_types.wait_for_complete(
            SearchResourceSlotTypesAction(querier=querier)
        )
    )

    nodes = [ResourceSlotTypeGQL.from_data(data) for data in action_result.items]
    edges = [ResourceSlotTypeEdgeGQL(node=node, cursor=encode_cursor(node.id)) for node in nodes]

    return ResourceSlotTypeConnectionGQL(
        edges=edges,
        page_info=strawberry.relay.PageInfo(
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=action_result.total_count,
    )


async def fetch_resource_slot_type(
    info: Info[StrawberryGQLContext],
    slot_name: str,
) -> ResourceSlotTypeGQL:
    """Fetch a single resource slot type by slot_name (used by Node resolution and root query)."""
    action_result = (
        await info.context.processors.resource_slot.get_resource_slot_type.wait_for_complete(
            GetResourceSlotTypeAction(slot_name=slot_name)
        )
    )
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
    action_result = (
        await info.context.processors.resource_slot.get_kernel_allocations.wait_for_complete(
            GetKernelAllocationsAction(kernel_id=_uuid.UUID(kernel_id))
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
    action_result = (
        await info.context.processors.resource_slot.get_kernel_allocations.wait_for_complete(
            GetKernelAllocationsAction(kernel_id=_uuid.UUID(kernel_id_str))
        )
    )
    for data in action_result.items:
        if data.slot_name == slot_name:
            return KernelResourceAllocationGQL.from_data(data)
    return None


# ========== Raw data helpers for Node.resolve_nodes ==========
# These return raw data types so that resolve_nodes can call cls.from_data(),
# which enables mypy to correctly infer the return type as Iterable[Self | None].


async def load_resource_slot_type_data(
    info: Info[StrawberryGQLContext],
    slot_name: str,
) -> ResourceSlotTypeData:
    """Load raw ResourceSlotTypeData for a single slot_name (used by Node.resolve_nodes)."""
    action_result = (
        await info.context.processors.resource_slot.get_resource_slot_type.wait_for_complete(
            GetResourceSlotTypeAction(slot_name=slot_name)
        )
    )
    return ResourceSlotTypeData(
        slot_name=action_result.item.slot_name,
        slot_type=action_result.item.slot_type,
        display_name=action_result.item.display_name,
        description=action_result.item.description,
        display_unit=action_result.item.display_unit,
        display_icon=action_result.item.display_icon,
        number_format=action_result.item.number_format,
        rank=action_result.item.rank,
    )


async def load_agent_resource_data(
    info: Info[StrawberryGQLContext],
    agent_id: str,
    slot_name: str,
) -> AgentResourceData | None:
    """Load raw AgentResourceData for a single agent+slot (used by Node.resolve_nodes)."""
    action_result = (
        await info.context.processors.resource_slot.get_agent_resources.wait_for_complete(
            GetAgentResourcesAction(agent_id=agent_id)
        )
    )
    for data in action_result.items:
        if data.slot_name == slot_name:
            return data
    return None


async def load_kernel_allocation_data(
    info: Info[StrawberryGQLContext],
    kernel_id_str: str,
    slot_name: str,
) -> ResourceAllocationData | None:
    """Load raw ResourceAllocationData for a single kernel+slot (used by Node.resolve_nodes)."""
    action_result = (
        await info.context.processors.resource_slot.get_kernel_allocations.wait_for_complete(
            GetKernelAllocationsAction(kernel_id=_uuid.UUID(kernel_id_str))
        )
    )
    for data in action_result.items:
        if data.slot_name == slot_name:
            return data
    return None
