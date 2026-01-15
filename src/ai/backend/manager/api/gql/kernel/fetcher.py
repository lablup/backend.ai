"""Fetcher functions for kernel queries."""

from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING, Optional

from strawberry import Info
from strawberry.relay import PageInfo

from ai.backend.common.types import AgentId
from ai.backend.manager.api.gql.adapter import PaginationOptions, PaginationSpec
from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.repositories.base import QueryCondition
from ai.backend.manager.repositories.scheduler.options import KernelConditions, KernelOrders
from ai.backend.manager.services.session.actions.search_kernel import SearchKernelsAction

from .types import (
    KernelConnectionV2GQL,
    KernelEdgeGQL,
    KernelFilterGQL,
    KernelGQL,
    KernelOrderByGQL,
)

if TYPE_CHECKING:
    from ai.backend.manager.api.gql.types import StrawberryGQLContext


@lru_cache(maxsize=1)
def _get_kernel_pagination_spec() -> PaginationSpec:
    """Get pagination specification for kernels.

    Returns a cached PaginationSpec with:
    - Forward pagination: created_at DESC (newest first)
    - Backward pagination: created_at ASC
    """
    return PaginationSpec(
        forward_order=KernelOrders.created_at(ascending=False),
        backward_order=KernelOrders.created_at(ascending=True),
        forward_condition_factory=KernelConditions.by_cursor_forward,
        backward_condition_factory=KernelConditions.by_cursor_backward,
    )


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
    nodes = [KernelGQL.from_kernel_info(kernel_info) for kernel_info in action_result.data]
    edges = [KernelEdgeGQL(node=node, cursor=encode_cursor(str(node.row_id))) for node in nodes]

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
