"""User V2 GraphQL data fetcher functions."""

from __future__ import annotations

from uuid import UUID

from strawberry import Info

from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.user_v2.types import (
    UserV2Connection,
    UserV2Filter,
    UserV2OrderBy,
)


async def fetch_admin_users(
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
    """Fetch all users with optional filtering, ordering, and pagination.

    This is the admin-level fetcher that returns all users in the system.

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

    Raises:
        NotImplementedError: This fetcher is not yet implemented.
    """
    raise NotImplementedError("fetch_admin_users is not yet implemented")


async def fetch_domain_users(
    info: Info[StrawberryGQLContext],
    domain_name: str,
    filter: UserV2Filter | None = None,
    order_by: list[UserV2OrderBy] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> UserV2Connection:
    """Fetch users within a specific domain.

    Args:
        info: Strawberry GraphQL context.
        domain_name: Name of the domain to filter by.
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

    Raises:
        NotImplementedError: This fetcher is not yet implemented.
    """
    raise NotImplementedError("fetch_domain_users is not yet implemented")


async def fetch_project_users(
    info: Info[StrawberryGQLContext],
    project_id: UUID,
    filter: UserV2Filter | None = None,
    order_by: list[UserV2OrderBy] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> UserV2Connection:
    """Fetch users within a specific project.

    Args:
        info: Strawberry GraphQL context.
        project_id: UUID of the project to filter by.
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

    Raises:
        NotImplementedError: This fetcher is not yet implemented.
    """
    raise NotImplementedError("fetch_project_users is not yet implemented")
