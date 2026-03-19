"""Domain Fair Share fetcher functions."""

from __future__ import annotations

from strawberry import Info
from strawberry.relay import PageInfo

from ai.backend.common.dto.manager.v2.fair_share.request import (
    GetDomainFairShareInput,
    SearchDomainFairSharesInput,
)
from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.api.gql.fair_share.types import (
    DomainFairShareConnection,
    DomainFairShareEdge,
    DomainFairShareFilter,
    DomainFairShareGQL,
    DomainFairShareOrderBy,
    RGDomainFairShareFilter,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.repositories.fair_share.types import DomainFairShareSearchScope


async def fetch_domain_fair_shares(
    info: Info[StrawberryGQLContext],
    filter: DomainFairShareFilter | None = None,
    order_by: list[DomainFairShareOrderBy] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> DomainFairShareConnection:
    """Fetch domain fair shares with optional filtering, ordering, and pagination.

    Args:
        info: GraphQL context info
        filter: Optional filter criteria
        order_by: Optional ordering specification
        before/after/first/last: Cursor-based pagination parameters
        limit/offset: Offset-based pagination parameters
    """
    pydantic_filter = filter.to_pydantic() if filter else None
    pydantic_orders = [o.to_pydantic() for o in order_by] if order_by else None

    payload = await info.context.adapters.fair_share.search_domain(
        SearchDomainFairSharesInput(
            filter=pydantic_filter,
            order=pydantic_orders,
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        )
    )

    nodes = [DomainFairShareGQL.from_node(item) for item in payload.items]
    edges = [DomainFairShareEdge(node=node, cursor=encode_cursor(str(node.id))) for node in nodes]

    return DomainFairShareConnection(
        edges=edges,
        page_info=PageInfo(
            has_next_page=len(payload.items) > 0 and (first is not None or limit is not None),
            has_previous_page=(offset or 0) > 0 or last is not None,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=payload.total_count,
    )


async def fetch_rg_domain_fair_shares(
    info: Info[StrawberryGQLContext],
    scope: DomainFairShareSearchScope,
    filter: RGDomainFairShareFilter | None = None,
    order_by: list[DomainFairShareOrderBy] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> DomainFairShareConnection:
    """Fetch domain fair shares using resource group scope.

    Returns all domains in the scope, including those without records (with defaults).
    """
    pydantic_filter = filter.to_pydantic() if filter else None
    pydantic_orders = [o.to_pydantic() for o in order_by] if order_by else None

    payload = await info.context.adapters.fair_share.search_rg_domain(
        SearchDomainFairSharesInput(
            filter=pydantic_filter,
            order=pydantic_orders,
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        ),
        resource_group=scope.resource_group,
    )

    nodes = [DomainFairShareGQL.from_node(item) for item in payload.items]
    edges = [DomainFairShareEdge(node=node, cursor=encode_cursor(str(node.id))) for node in nodes]

    return DomainFairShareConnection(
        edges=edges,
        page_info=PageInfo(
            has_next_page=len(payload.items) > 0 and (first is not None or limit is not None),
            has_previous_page=(offset or 0) > 0 or last is not None,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=payload.total_count,
    )


async def fetch_single_domain_fair_share(
    info: Info[StrawberryGQLContext],
    resource_group_name: str,
    domain_name: str,
) -> DomainFairShareGQL:
    """Fetch a single domain fair share record.

    Returns the fair share record for the specified domain and resource group.
    If no record exists, returns a default-generated object (adapter handles defaults).
    """
    payload = await info.context.adapters.fair_share.get_domain(
        GetDomainFairShareInput(
            resource_group=resource_group_name,
            domain_name=domain_name,
        )
    )

    return DomainFairShareGQL.from_node(payload.item)  # type: ignore[arg-type]
