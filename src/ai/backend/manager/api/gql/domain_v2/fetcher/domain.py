"""Domain V2 GraphQL data fetcher functions."""

from __future__ import annotations

from functools import lru_cache

from strawberry import Info
from strawberry.relay import PageInfo

from ai.backend.manager.api.gql.adapter import PaginationOptions, PaginationSpec
from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.api.gql.domain_v2.types import (
    DomainV2Connection,
    DomainV2Edge,
    DomainV2Filter,
    DomainV2GQL,
    DomainV2OrderBy,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.repositories.domain.options import DomainConditions, DomainOrders
from ai.backend.manager.repositories.domain.types import DomainSearchScope
from ai.backend.manager.services.domain.actions.get_domain import GetDomainAction
from ai.backend.manager.services.domain.actions.search_domains import SearchDomainsAction
from ai.backend.manager.services.domain.actions.search_rg_domains import SearchRGDomainsAction


@lru_cache(maxsize=1)
def get_domain_pagination_spec() -> PaginationSpec:
    """Cached pagination spec for domain queries."""
    return PaginationSpec(
        forward_order=DomainOrders.created_at(ascending=False),
        backward_order=DomainOrders.created_at(ascending=True),
        forward_condition_factory=DomainConditions.by_cursor_forward,
        backward_condition_factory=DomainConditions.by_cursor_backward,
        tiebreaker_order=DomainRow.name.asc(),
    )


async def fetch_domain(
    info: Info[StrawberryGQLContext],
    domain_name: str,
) -> DomainV2GQL:
    """Fetch a single domain by name.

    Args:
        info: Strawberry GraphQL context.
        domain_name: Name of the domain to retrieve.

    Returns:
        DomainV2GQL object.

    Raises:
        DomainNotFound: If the domain does not exist.
    """
    processors = info.context.processors

    # Execute via processor
    action_result = await processors.domain.get_domain.wait_for_complete(
        GetDomainAction(domain_name=domain_name)
    )

    return DomainV2GQL.from_data(action_result.data)


async def fetch_admin_domains(
    info: Info[StrawberryGQLContext],
    filter: DomainV2Filter | None = None,
    order_by: list[DomainV2OrderBy] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> DomainV2Connection:
    """Fetch all domains with optional filtering, ordering, and pagination.

    This is the admin-level fetcher that returns all domains in the system.

    Args:
        info: Strawberry GraphQL context.
        filter: Optional filter criteria.
        order_by: Optional ordering specification.
        before: Cursor for backward pagination.
        after: Cursor for forward pagination.
        first: Number of items from the start.
        last: Number of items from the end.
        limit: Maximum number of items (offset-based).
        offset: Starting position (offset-based).

    Returns:
        DomainV2Connection with paginated domain records.
    """
    processors = info.context.processors

    # Build querier
    querier = info.context.gql_adapter.build_querier(
        PaginationOptions(
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        ),
        get_domain_pagination_spec(),
        filter=filter,
        order_by=order_by,
        base_conditions=None,
    )

    # Execute via processor
    action_result = await processors.domain.search_domains.wait_for_complete(
        SearchDomainsAction(querier=querier)
    )

    # Build connection
    nodes = [DomainV2GQL.from_data(data) for data in action_result.items]
    edges = [DomainV2Edge(node=node, cursor=encode_cursor(str(node.id))) for node in nodes]

    return DomainV2Connection(
        edges=edges,
        page_info=PageInfo(
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=action_result.total_count,
    )


async def fetch_rg_domains(
    info: Info[StrawberryGQLContext],
    scope: DomainSearchScope,
    filter: DomainV2Filter | None = None,
    order_by: list[DomainV2OrderBy] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> DomainV2Connection:
    """Fetch domains within a resource group scope.

    This fetcher returns only domains that are associated with the specified resource group
    through the sgroups_for_domains relationship.

    Args:
        info: Strawberry GraphQL context.
        scope: DomainSearchScope containing resource_group filter.
        filter: Optional filter criteria.
        order_by: Optional ordering specification.
        before: Cursor for backward pagination.
        after: Cursor for forward pagination.
        first: Number of items from the start.
        last: Number of items from the end.
        limit: Maximum number of items (offset-based).
        offset: Starting position (offset-based).

    Returns:
        DomainV2Connection with paginated domain records.
    """
    processors = info.context.processors

    # Build querier
    querier = info.context.gql_adapter.build_querier(
        PaginationOptions(
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        ),
        get_domain_pagination_spec(),
        filter=filter,
        order_by=order_by,
        base_conditions=None,
    )

    # Execute via processor with scope
    action_result = await processors.domain.search_rg_domains.wait_for_complete(
        SearchRGDomainsAction(scope=scope, querier=querier)
    )

    # Build connection
    nodes = [DomainV2GQL.from_data(data) for data in action_result.items]
    edges = [DomainV2Edge(node=node, cursor=encode_cursor(str(node.id))) for node in nodes]

    return DomainV2Connection(
        edges=edges,
        page_info=PageInfo(
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=action_result.total_count,
    )
