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
from ai.backend.manager.models.resource_slot import (
    AgentResourceRow,
    ResourceAllocationRow,
    ResourceSlotTypeRow,
)
from ai.backend.manager.repositories.resource_slot.query import (
    AgentResourceQueryConditions,
    AgentResourceQueryOrders,
    CursorConditions,
    QueryOrders,
    ResourceAllocationQueryConditions,
    ResourceAllocationQueryOrders,
)
from ai.backend.manager.services.resource_slot.actions.get_agent_resource_by_slot import (
    GetAgentResourceBySlotAction,
)
from ai.backend.manager.services.resource_slot.actions.get_kernel_allocation_by_slot import (
    GetKernelAllocationBySlotAction,
)
from ai.backend.manager.services.resource_slot.actions.get_resource_slot_type import (
    GetResourceSlotTypeAction,
)
from ai.backend.manager.services.resource_slot.actions.search_agent_resources import (
    SearchAgentResourcesAction,
)
from ai.backend.manager.services.resource_slot.actions.search_resource_allocations import (
    SearchResourceAllocationsAction,
)
from ai.backend.manager.services.resource_slot.actions.search_resource_slot_types import (
    SearchResourceSlotTypesAction,
)

from .types import (
    AgentResourceConnectionGQL,
    AgentResourceSlotEdgeGQL,
    AgentResourceSlotFilterGQL,
    AgentResourceSlotGQL,
    AgentResourceSlotOrderByGQL,
    KernelResourceAllocationEdgeGQL,
    KernelResourceAllocationFilterGQL,
    KernelResourceAllocationGQL,
    KernelResourceAllocationOrderByGQL,
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


@lru_cache(maxsize=1)
def _get_agent_resource_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=AgentResourceQueryOrders.slot_name(ascending=True),
        backward_order=AgentResourceQueryOrders.slot_name(ascending=False),
        forward_condition_factory=AgentResourceQueryConditions.by_cursor_forward,
        backward_condition_factory=AgentResourceQueryConditions.by_cursor_backward,
        tiebreaker_order=AgentResourceRow.slot_name.asc(),
    )


@lru_cache(maxsize=1)
def _get_resource_allocation_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=ResourceAllocationQueryOrders.slot_name(ascending=True),
        backward_order=ResourceAllocationQueryOrders.slot_name(ascending=False),
        forward_condition_factory=ResourceAllocationQueryConditions.by_cursor_forward,
        backward_condition_factory=ResourceAllocationQueryConditions.by_cursor_backward,
        tiebreaker_order=ResourceAllocationRow.slot_name.asc(),
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
    filter: AgentResourceSlotFilterGQL | None = None,
    order_by: list[AgentResourceSlotOrderByGQL] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> AgentResourceConnectionGQL:
    """Fetch per-slot resource entries for a given agent with pagination and filtering."""
    querier = info.context.gql_adapter.build_querier(
        PaginationOptions(
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        ),
        pagination_spec=_get_agent_resource_pagination_spec(),
        filter=filter,
        order_by=order_by,
        base_conditions=[AgentResourceQueryConditions.by_agent_id(agent_id)],
    )

    action_result = (
        await info.context.processors.resource_slot.search_agent_resources.wait_for_complete(
            SearchAgentResourcesAction(querier=querier)
        )
    )

    edges = []
    for data in action_result.items:
        node = AgentResourceSlotGQL.from_data(data)
        cursor = encode_cursor(data.slot_name)
        edges.append(AgentResourceSlotEdgeGQL(node=node, cursor=cursor))

    return AgentResourceConnectionGQL(
        count=action_result.total_count,
        edges=edges,
        page_info=strawberry.relay.PageInfo(
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
    )


async def fetch_kernel_allocations(
    info: Info[StrawberryGQLContext],
    kernel_id: str,
    filter: KernelResourceAllocationFilterGQL | None = None,
    order_by: list[KernelResourceAllocationOrderByGQL] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> ResourceAllocationConnectionGQL:
    """Fetch per-slot allocation entries for a kernel with pagination and filtering."""
    querier = info.context.gql_adapter.build_querier(
        PaginationOptions(
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        ),
        pagination_spec=_get_resource_allocation_pagination_spec(),
        filter=filter,
        order_by=order_by,
        base_conditions=[ResourceAllocationQueryConditions.by_kernel_id(_uuid.UUID(kernel_id))],
    )

    action_result = (
        await info.context.processors.resource_slot.search_resource_allocations.wait_for_complete(
            SearchResourceAllocationsAction(querier=querier)
        )
    )

    edges = []
    for data in action_result.items:
        node = KernelResourceAllocationGQL.from_data(data)
        cursor = encode_cursor(data.slot_name)
        edges.append(KernelResourceAllocationEdgeGQL(node=node, cursor=cursor))

    return ResourceAllocationConnectionGQL(
        count=action_result.total_count,
        edges=edges,
        page_info=strawberry.relay.PageInfo(
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
    )


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
    return action_result.item


async def load_agent_resource_data(
    info: Info[StrawberryGQLContext],
    agent_id: str,
    slot_name: str,
) -> AgentResourceData:
    """Load raw AgentResourceData for a single agent+slot (used by Node.resolve_nodes).

    Raises AgentResourceNotFound if the entry does not exist.
    """
    action_result = (
        await info.context.processors.resource_slot.get_agent_resource_by_slot.wait_for_complete(
            GetAgentResourceBySlotAction(agent_id=agent_id, slot_name=slot_name)
        )
    )
    return action_result.item


async def load_kernel_allocation_data(
    info: Info[StrawberryGQLContext],
    kernel_id_str: str,
    slot_name: str,
) -> ResourceAllocationData:
    """Load raw ResourceAllocationData for a single kernel+slot (used by Node.resolve_nodes).

    Raises ResourceAllocationNotFound if the entry does not exist.
    """
    action_result = (
        await info.context.processors.resource_slot.get_kernel_allocation_by_slot.wait_for_complete(
            GetKernelAllocationBySlotAction(
                kernel_id=_uuid.UUID(kernel_id_str), slot_name=slot_name
            )
        )
    )
    return action_result.item
