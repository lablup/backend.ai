from __future__ import annotations

from typing import Optional
from uuid import UUID

import strawberry
from strawberry import Info

from ai.backend.manager.api.gql.base import UUIDFilter
from ai.backend.manager.api.gql.kernel.fetcher import fetch_kernels
from ai.backend.manager.api.gql.kernel.types import (
    KernelConnectionV2GQL,
    KernelFilterGQL,
    KernelOrderByGQL,
    KernelV2GQL,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.errors.kernel import TooManyKernelsFound


@strawberry.field(description="Added in 26.1.0. Query a single kernel by ID.")
async def kernel_v2(
    info: Info[StrawberryGQLContext],
    id: UUID,
) -> Optional[KernelV2GQL]:
    result = await fetch_kernels(info, filter=KernelFilterGQL(id=UUIDFilter(equals=id)), limit=1)
    if len(result.edges) >= 2:
        raise TooManyKernelsFound
    if result.edges:
        return result.edges[0].node
    return None


@strawberry.field(description="Added in 26.1.0. Query kernels with pagination and filtering.")
async def kernels_v2(
    info: Info[StrawberryGQLContext],
    filter: Optional[KernelFilterGQL] = None,
    order_by: Optional[list[KernelOrderByGQL]] = None,
    before: Optional[str] = None,
    after: Optional[str] = None,
    first: Optional[int] = None,
    last: Optional[int] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> KernelConnectionV2GQL:
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
