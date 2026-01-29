from __future__ import annotations

from functools import lru_cache

import strawberry
from strawberry import Info

from ai.backend.common.types import KernelId
from ai.backend.manager.api.gql.adapter import PaginationOptions, PaginationSpec
from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.api.gql.kernel.types import (
    KernelConnectionV2GQL,
    KernelEdgeGQL,
    KernelFilterGQL,
    KernelOrderByGQL,
    KernelV2GQL,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.models.kernel import KernelRow
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
    edges = [KernelEdgeGQL(node=node, cursor=encode_cursor(node.id)) for node in nodes]

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
    kernel_id: KernelId,
) -> KernelV2GQL | None:
    """Fetch a single kernel by ID using dataloader."""
    kernel_info = await info.context.data_loaders.kernel_loader.load(kernel_id)
    if kernel_info is None:
        return None
    return KernelV2GQL.from_kernel_info(kernel_info)
