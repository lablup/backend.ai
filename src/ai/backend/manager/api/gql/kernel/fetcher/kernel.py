from __future__ import annotations

from functools import lru_cache
from typing import Optional
from uuid import UUID

import strawberry
from strawberry import Info
from strawberry.relay import PageInfo

from ai.backend.common.types import AgentId
from ai.backend.manager.api.gql.adapter import PaginationOptions, PaginationSpec
from ai.backend.manager.api.gql.base import encode_cursor, to_global_id
from ai.backend.manager.api.gql.kernel.types import (
    KernelConnectionV2GQL,
    KernelEdgeGQL,
    KernelFilterGQL,
    KernelOrderByGQL,
    KernelV2GQL,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.repositories.base import QueryCondition
from ai.backend.manager.repositories.scheduler.options import KernelConditions
from ai.backend.manager.services.session.actions.search_kernel import SearchKernelsAction


@lru_cache(maxsize=1)
def _get_kernel_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=KernelRow.created_at.desc(),
        backward_order=KernelRow.created_at.asc(),
        forward_condition_factory=KernelConditions.by_cursor_forward,
        backward_condition_factory=KernelConditions.by_cursor_backward,
    )


async def fetch_kernels(
    info: Info[StrawberryGQLContext],
    filter: KernelFilterGQL | None = None,
    order_by: list[KernelOrderByGQL] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> KernelConnectionV2GQL:
    querier = info.context.gql_adapter.build_querier(
        PaginationOptions(
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        ),
        pagination_spec=_get_kernel_pagination_spec(),
        filter=filter,
        order_by=order_by,
    )

    action_result = await info.context.processors.session.search_kernels.wait_for_complete(
        SearchKernelsAction(querier=querier)
    )
    nodes = [KernelV2GQL.from_kernel_info(kernel_info) for kernel_info in action_result.data]
    edges = [KernelEdgeGQL(node=node, cursor=to_global_id(KernelV2GQL, node.id)) for node in nodes]

    return KernelConnectionV2GQL(
        edges=edges,
        page_info=strawberry.relay.PageInfo(
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=action_result.total_count,
    )


async def fetch_kernel(
    info: Info[StrawberryGQLContext],
    kernel_id: UUID,
) -> KernelV2GQL | None:
    """Fetch a single kernel by ID."""
    filter = KernelFilterGQL(id=kernel_id)
    querier = info.context.gql_adapter.build_querier(
        PaginationOptions(limit=1),
        pagination_spec=_get_kernel_pagination_spec(),
        filter=filter,
        order_by=None,
    )

    action_result = await info.context.processors.session.search_kernels.wait_for_complete(
        SearchKernelsAction(querier=querier)
    )

    if not action_result.data:
        return None

    return KernelV2GQL.from_kernel_info(action_result.data[0])


async def fetch_kernels_by_agent(
    info: Info[StrawberryGQLContext],
    agent_id: AgentId,
    filter: Optional[KernelFilterGQL] = None,
    order_by: Optional[list[KernelOrderByGQL]] = None,
    before: Optional[str] = None,
    after: Optional[str] = None,
    first: Optional[int] = None,
    last: Optional[int] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    resource_occupied_only: bool = False,
) -> KernelConnectionV2GQL:
    """Fetch kernels associated with a specific agent.

    Args:
        info: GraphQL context info
        agent_id: The ID of the agent to fetch kernels for
        filter: Optional filter criteria
        order_by: Optional ordering specification
        before/after/first/last: Cursor-based pagination parameters
        limit/offset: Offset-based pagination parameters
        resource_occupied_only: If True, only return kernels that are occupying resources

    Returns:
        KernelConnectionV2GQL with paginated kernel results
    """
    processors = info.context.processors

    # Build base conditions - filter by agent_id
    base_conditions: list[QueryCondition] = [KernelConditions.by_agent_ids([str(agent_id)])]

    # Add resource_occupied filter if requested
    if resource_occupied_only:
        base_conditions.append(
            KernelConditions.by_statuses(list(KernelStatus.resource_occupied_statuses()))
        )

    # Build querier using gql_adapter
    querier = info.context.gql_adapter.build_querier(
        PaginationOptions(
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        ),
        _get_kernel_pagination_spec(),
        filter=filter,
        order_by=order_by,
        base_conditions=base_conditions,
    )

    # Execute search action
    action_result = await processors.session.search_kernels.wait_for_complete(
        SearchKernelsAction(querier=querier)
    )

    # Convert to GraphQL types
    nodes = [KernelV2GQL.from_kernel_info(kernel_info) for kernel_info in action_result.data]
    edges = [KernelEdgeGQL(node=node, cursor=encode_cursor(str(node.id))) for node in nodes]

    return KernelConnectionV2GQL(
        count=action_result.total_count,
        edges=edges,
        page_info=PageInfo(
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
    )
