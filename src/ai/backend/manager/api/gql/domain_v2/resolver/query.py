"""Domain V2 GraphQL query resolvers."""

from __future__ import annotations

import strawberry
from strawberry import Info

from ai.backend.manager.api.gql.domain_v2.fetcher import (
    fetch_admin_domains,
    fetch_domain,
    fetch_rg_domains,
)
from ai.backend.manager.api.gql.domain_v2.types import (
    DomainV2Connection,
    DomainV2Filter,
    DomainV2GQL,
    DomainV2OrderBy,
)
from ai.backend.manager.api.gql.types import ResourceGroupDomainScope, StrawberryGQLContext
from ai.backend.manager.repositories.domain.types import DomainSearchScope


@strawberry.field(
    description=(
        "Added in 26.2.0. Get a single domain by name. Returns an error if domain is not found."
    )
)  # type: ignore[misc]
async def domain_v2(
    info: Info[StrawberryGQLContext],
    domain_name: str,
) -> DomainV2GQL:
    """Get a single domain by name.

    Args:
        info: Strawberry GraphQL context.
        domain_name: Name of the domain to retrieve.

    Returns:
        DomainV2GQL object.

    Raises:
        DomainNotFound: If the domain with the given name does not exist.
    """
    return await fetch_domain(info, domain_name=domain_name)


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
) -> DomainV2Connection:
    """List all domains with optional filtering, ordering, and pagination.

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
    return await fetch_admin_domains(
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
) -> DomainV2Connection:
    """List domains within a resource group scope.

    Args:
        info: Strawberry GraphQL context.
        scope: Resource group scope for filtering domains.
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
    # Convert GraphQL scope to repository scope
    repo_scope = DomainSearchScope(resource_group=scope.resource_group)

    return await fetch_rg_domains(
        info,
        scope=repo_scope,
        filter=filter,
        order_by=order_by,
        before=before,
        after=after,
        first=first,
        last=last,
        limit=limit,
        offset=offset,
    )
