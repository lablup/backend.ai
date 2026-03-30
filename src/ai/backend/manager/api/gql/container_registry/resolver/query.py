"""Container Registry V2 GraphQL query resolvers."""

from __future__ import annotations

import strawberry
from strawberry import Info
from strawberry.relay import PageInfo

from ai.backend.common.dto.manager.v2.container_registry.request import (
    AdminSearchContainerRegistriesInput,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.api.gql.container_registry.filters import (
    ContainerRegistryV2Filter,
    ContainerRegistryV2OrderBy,
)
from ai.backend.manager.api.gql.container_registry.types import (
    ContainerRegistryGQL,
    ContainerRegistryV2Connection,
)
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_root_field,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="List container registries with filtering, ordering, and pagination (admin only).",
    )
)  # type: ignore[misc]
async def admin_container_registries_v2(
    info: Info[StrawberryGQLContext],
    filter: ContainerRegistryV2Filter | None = None,
    order_by: list[ContainerRegistryV2OrderBy] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> ContainerRegistryV2Connection | None:
    check_admin_only()
    payload = await info.context.adapters.container_registry.admin_search(
        AdminSearchContainerRegistriesInput(
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
    nodes = [ContainerRegistryGQL.from_pydantic(item) for item in payload.items]
    edges = [strawberry.relay.Edge(node=n, cursor=encode_cursor(str(n.id))) for n in nodes]
    return ContainerRegistryV2Connection(
        edges=edges,
        page_info=PageInfo(
            has_next_page=payload.has_next_page,
            has_previous_page=payload.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=payload.total_count,
    )
