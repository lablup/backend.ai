from __future__ import annotations

from uuid import UUID

import strawberry
from strawberry import Info

from ai.backend.common.types import KernelId, SessionId
from ai.backend.manager.api.gql.kernel.fetcher import fetch_kernel, fetch_kernels
from ai.backend.manager.api.gql.kernel.types import (
    KernelV2ConnectionGQL,
    KernelV2FilterGQL,
    KernelV2OrderByGQL,
    KernelV2GQL,
)
from ai.backend.manager.api.gql.scheduling_history import SessionScope
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only
from ai.backend.manager.repositories.scheduler.options import KernelConditions


@strawberry.field(description="Added in 26.2.0. Query a single kernel by ID.")  # type: ignore[misc]
async def kernel_v2(
    info: Info[StrawberryGQLContext],
    id: UUID,
) -> KernelV2GQL | None:
    return await fetch_kernel(info, KernelId(id))


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
) -> KernelV2ConnectionGQL:
    check_admin_only()
    return await fetch_kernels(
        info,
        filter=filter,
        order_by=order_by,
        before=before,
        after=after,
        first=first,
        last=last,
        limit=limit,
        offset=offset,
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
) -> KernelV2ConnectionGQL:
    base_conditions = [KernelConditions.by_session_ids([SessionId(scope.session_id)])]
    return await fetch_kernels(
        info,
        filter=filter,
        order_by=order_by,
        before=before,
        after=after,
        first=first,
        last=last,
        limit=limit,
        offset=offset,
        base_conditions=base_conditions,
    )
