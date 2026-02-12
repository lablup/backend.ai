"""Project V2 GraphQL query resolvers."""

from __future__ import annotations

from uuid import UUID

import strawberry
from strawberry import Info

from ai.backend.manager.api.gql.domain_v2.types import DomainV2GQL
from ai.backend.manager.api.gql.project_v2.fetcher import (
    fetch_admin_projects,
    fetch_domain_projects,
    fetch_project,
    fetch_project_domain,
)
from ai.backend.manager.api.gql.project_v2.types import (
    DomainProjectScope,
    ProjectV2Connection,
    ProjectV2Filter,
    ProjectV2GQL,
    ProjectV2OrderBy,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext


@strawberry.field(
    description=(
        "Added in 26.2.0. Get a single project by ID. Returns an error if project is not found."
    )
)  # type: ignore[misc]
async def project_v2(
    info: Info[StrawberryGQLContext],
    project_id: UUID,
) -> ProjectV2GQL | None:
    """Get a single project by UUID.

    Args:
        info: Strawberry GraphQL context.
        project_id: UUID of the project to retrieve.

    Returns:
        ProjectV2GQL object.

    Raises:
        ProjectNotFound: If the project with the given UUID does not exist.
    """
    return await fetch_project(info, project_id=project_id)


@strawberry.field(
    description=(
        "Added in 26.2.0. List all projects with filtering and pagination (admin only). "
        "Requires superadmin privileges."
    )
)  # type: ignore[misc]
async def admin_projects_v2(
    info: Info[StrawberryGQLContext],
    filter: ProjectV2Filter | None = None,
    order_by: list[ProjectV2OrderBy] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> ProjectV2Connection | None:
    """List all projects with optional filtering, ordering, and pagination.

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
        ProjectV2Connection with paginated project records.
    """
    return await fetch_admin_projects(
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
    description=(
        "Added in 26.2.0. List projects within a specific domain. "
        "Requires domain admin privileges or higher."
    )
)  # type: ignore[misc]
async def domain_projects_v2(
    info: Info[StrawberryGQLContext],
    scope: DomainProjectScope,
    filter: ProjectV2Filter | None = None,
    order_by: list[ProjectV2OrderBy] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> ProjectV2Connection | None:
    """List projects within a specific domain.

    Args:
        info: Strawberry GraphQL context.
        scope: Domain scope specifying which domain to query.
        filter: Optional additional filter criteria.
        order_by: Optional ordering specification.
        before: Cursor for backward pagination.
        after: Cursor for forward pagination.
        first: Number of items from the start.
        last: Number of items from the end.
        limit: Maximum number of items (offset-based).
        offset: Starting position (offset-based).

    Returns:
        ProjectV2Connection with paginated project records from the domain.
    """
    from ai.backend.manager.repositories.group.types import DomainProjectSearchScope

    return await fetch_domain_projects(
        info,
        scope=DomainProjectSearchScope(domain_name=scope.domain_name),
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
    description=(
        "Added in 26.2.0. Get the domain that a project belongs to. "
        "Returns an error if project or domain is not found."
    )
)  # type: ignore[misc]
async def project_domain_v2(
    info: Info[StrawberryGQLContext],
    project_id: UUID,
) -> DomainV2GQL | None:
    """Get the domain that a project belongs to.

    Args:
        info: Strawberry GraphQL context.
        project_id: UUID of the project.

    Returns:
        DomainV2GQL object for the project's domain.

    Raises:
        ProjectNotFound: If the project with the given UUID does not exist.
        DomainNotFound: If the project's domain does not exist.
    """
    return await fetch_project_domain(info, project_id=project_id)
