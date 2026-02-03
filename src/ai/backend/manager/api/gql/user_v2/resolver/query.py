"""User V2 GraphQL query resolvers."""

from __future__ import annotations

from uuid import UUID

import strawberry
from strawberry import Info

from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.user_v2.fetcher import (
    fetch_admin_users,
    fetch_domain_users,
    fetch_project_users,
)
from ai.backend.manager.api.gql.user_v2.types import (
    DomainUserScope,
    ProjectUserScope,
    UserV2Connection,
    UserV2Filter,
    UserV2GQL,
    UserV2OrderBy,
)


@strawberry.field(
    description=(
        "Added in 26.2.0. Get a single user by UUID (admin only). "
        "Requires superadmin privileges. Returns an error if user is not found."
    )
)  # type: ignore[misc]
async def admin_user_v2(
    info: Info[StrawberryGQLContext],
    user_id: UUID,
) -> UserV2GQL:
    """Get a single user by UUID.

    Args:
        info: Strawberry GraphQL context.
        user_id: UUID of the user to retrieve.

    Returns:
        UserV2GQL object.

    Raises:
        NotImplementedError: This resolver is not yet implemented.
        UserNotFound: If the user with the given UUID does not exist.
    """
    raise NotImplementedError("admin_user_v2 is not yet implemented")


@strawberry.field(
    description=(
        "Added in 26.2.0. List all users with filtering and pagination (admin only). "
        "Requires superadmin privileges."
    )
)  # type: ignore[misc]
async def admin_users(
    info: Info[StrawberryGQLContext],
    filter: UserV2Filter | None = None,
    order_by: list[UserV2OrderBy] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> UserV2Connection:
    """List all users with optional filtering, ordering, and pagination.

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
        UserV2Connection with paginated user records.
    """
    return await fetch_admin_users(
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
        "Added in 26.2.0. List users within a specific domain. "
        "Requires domain admin privileges or higher."
    )
)  # type: ignore[misc]
async def domain_users(
    info: Info[StrawberryGQLContext],
    scope: DomainUserScope,
    filter: UserV2Filter | None = None,
    order_by: list[UserV2OrderBy] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> UserV2Connection:
    """List users within a specific domain.

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
        UserV2Connection with paginated user records from the domain.
    """
    return await fetch_domain_users(
        info,
        domain_name=scope.domain_name,
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
        "Added in 26.2.0. List users within a specific project. "
        "Requires project membership or higher privileges."
    )
)  # type: ignore[misc]
async def project_users(
    info: Info[StrawberryGQLContext],
    scope: ProjectUserScope,
    filter: UserV2Filter | None = None,
    order_by: list[UserV2OrderBy] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> UserV2Connection:
    """List users within a specific project.

    Args:
        info: Strawberry GraphQL context.
        scope: Project scope specifying which project to query.
        filter: Optional additional filter criteria.
        order_by: Optional ordering specification.
        before: Cursor for backward pagination.
        after: Cursor for forward pagination.
        first: Number of items from the start.
        last: Number of items from the end.
        limit: Maximum number of items (offset-based).
        offset: Starting position (offset-based).

    Returns:
        UserV2Connection with paginated user records from the project.
    """
    return await fetch_project_users(
        info,
        project_id=scope.project_id,
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
        "Added in 26.2.0. Get the current authenticated user's information. "
        "Returns the user associated with the current session. "
        "Returns an error if not authenticated."
    )
)  # type: ignore[misc]
async def user_v2(
    info: Info[StrawberryGQLContext],
) -> UserV2GQL:
    """Get the current authenticated user's information.

    Args:
        info: Strawberry GraphQL context.

    Returns:
        UserV2GQL for the current user.

    Raises:
        NotImplementedError: This resolver is not yet implemented.
        Unauthorized: If the user is not authenticated.
    """
    raise NotImplementedError("user_v2 is not yet implemented")
