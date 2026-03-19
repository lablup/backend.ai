"""Domain V2 GraphQL query resolvers."""

from __future__ import annotations

import strawberry
from strawberry import Info
from strawberry.relay import PageInfo

from ai.backend.common.dto.manager.v2.domain.request import AdminSearchDomainsInput
from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.api.gql.domain_v2.types import (
    DomainV2Connection,
    DomainV2Filter,
    DomainV2GQL,
    DomainV2OrderBy,
)
from ai.backend.manager.api.gql.types import ResourceGroupDomainScope, StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only
from ai.backend.manager.repositories.domain.types import DomainSearchScope


@strawberry.field(
    description=(
        "Added in 26.2.0. Get a single domain by name. Returns an error if domain is not found."
    )
)  # type: ignore[misc]
async def domain_v2(
    info: Info[StrawberryGQLContext],
    domain_name: str,
) -> DomainV2GQL | None:
    from ai.backend.manager.services.domain.actions.get_domain import GetDomainAction

    action_result = await info.context.processors.domain.get_domain.wait_for_complete(
        GetDomainAction(domain_name=domain_name)
    )
    return DomainV2GQL.from_data(action_result.data)


@strawberry.field(
    description=(
        "Added in 26.2.0. List all domains with filtering and pagination (admin only). "
        "Requires superadmin privileges."
    )
)  # type: ignore[misc]
async def admin_domains_v2(
    info: Info[StrawberryGQLContext],
    filter: DomainV2Filter | None = None,
    order_by: list[DomainV2OrderBy] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> DomainV2Connection | None:
    check_admin_only()
    payload = await info.context.adapters.domain.admin_search(
        AdminSearchDomainsInput(
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
    nodes = [DomainV2GQL.from_pydantic(node) for node in payload.items]
    edges = [strawberry.relay.Edge(node=node, cursor=encode_cursor(str(node.id))) for node in nodes]
    return DomainV2Connection(
        edges=edges,
        page_info=PageInfo(
            has_next_page=payload.has_next_page,
            has_previous_page=payload.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=payload.total_count,
    )


@strawberry.field(description="Added in 26.2.0. List domains within resource group scope.")  # type: ignore[misc]
async def rg_domains_v2(
    info: Info[StrawberryGQLContext],
    scope: ResourceGroupDomainScope,
    filter: DomainV2Filter | None = None,
    order_by: list[DomainV2OrderBy] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> DomainV2Connection | None:
    repo_scope = DomainSearchScope(resource_group=scope.resource_group_name)
    payload = await info.context.adapters.domain.search_rg_domains(
        scope=repo_scope,
        input=AdminSearchDomainsInput(
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
    nodes = [DomainV2GQL.from_pydantic(node) for node in payload.items]
    edges = [strawberry.relay.Edge(node=node, cursor=encode_cursor(str(node.id))) for node in nodes]
    return DomainV2Connection(
        edges=edges,
        page_info=PageInfo(
            has_next_page=payload.has_next_page,
            has_previous_page=payload.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=payload.total_count,
    )
