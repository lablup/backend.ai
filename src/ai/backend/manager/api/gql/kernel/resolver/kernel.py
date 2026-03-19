from __future__ import annotations

from uuid import UUID

import strawberry
from strawberry import Info

from ai.backend.common.dto.manager.v2.kernel.request import AdminSearchKernelsInput
from ai.backend.common.types import KernelId, SessionId
from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.api.gql.kernel.types import (
    KernelV2ConnectionGQL,
    KernelV2EdgeGQL,
    KernelV2FilterGQL,
    KernelV2GQL,
    KernelV2OrderByGQL,
)
from ai.backend.manager.api.gql.scheduling_history import SessionScope
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only


@strawberry.field(description="Added in 26.2.0. Query a single kernel by ID.")  # type: ignore[misc]
async def kernel_v2(
    info: Info[StrawberryGQLContext],
    id: UUID,
) -> KernelV2GQL | None:
    kernel_info = await info.context.data_loaders.kernel_loader.load(KernelId(id))
    if kernel_info is None:
        return None
    return KernelV2GQL.from_kernel_info(kernel_info)


@strawberry.field(
    description="Added in 26.2.0. Query kernels with pagination and filtering. (admin only)"
)  # type: ignore[misc]
async def admin_kernels_v2(
    info: Info[StrawberryGQLContext],
    filter: KernelV2FilterGQL | None = None,
    order_by: list[KernelV2OrderByGQL] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> KernelV2ConnectionGQL | None:
    check_admin_only()
    payload = await info.context.adapters.session.admin_search_kernels(
        AdminSearchKernelsInput(
            filter=filter.to_pydantic() if filter else None,
            order=[o.to_pydantic() for o in order_by] if order_by else None,
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        )
    )
    nodes = [KernelV2GQL.from_pydantic(node) for node in payload.items]
    edges = [KernelV2EdgeGQL(node=node, cursor=encode_cursor(node.id)) for node in nodes]
    return KernelV2ConnectionGQL(
        edges=edges,
        page_info=strawberry.relay.PageInfo(
            has_next_page=payload.has_next_page,
            has_previous_page=payload.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=payload.total_count,
    )


@strawberry.field(
    name="sessionKernelsV2",
    description="Added in 26.2.0. Query kernels within a specific session.",
)  # type: ignore[misc]
async def session_kernels_v2(
    info: Info[StrawberryGQLContext],
    scope: SessionScope,
    filter: KernelV2FilterGQL | None = None,
    order_by: list[KernelV2OrderByGQL] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> KernelV2ConnectionGQL | None:
    payload = await info.context.adapters.session.search_kernels_by_session(
        SessionId(scope.session_id),
        AdminSearchKernelsInput(
            filter=filter.to_pydantic() if filter else None,
            order=[o.to_pydantic() for o in order_by] if order_by else None,
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        ),
    )
    nodes = [KernelV2GQL.from_pydantic(node) for node in payload.items]
    edges = [KernelV2EdgeGQL(node=node, cursor=encode_cursor(node.id)) for node in nodes]
    return KernelV2ConnectionGQL(
        edges=edges,
        page_info=strawberry.relay.PageInfo(
            has_next_page=payload.has_next_page,
            has_previous_page=payload.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=payload.total_count,
    )
