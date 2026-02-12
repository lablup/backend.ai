"""User GraphQL query resolvers."""

from __future__ import annotations

from uuid import UUID

import strawberry
from strawberry import Info

from ai.backend.common.contexts.user import current_user
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.user.fetcher import (
    fetch_admin_users,
    fetch_domain_users,
    fetch_project_users,
)
from ai.backend.manager.api.gql.user.types import (
    DomainUserScopeGQL,
    ProjectUserScopeGQL,
    UserFilterGQL,
    UserOrderByGQL,
    UserV2Connection,
    UserV2GQL,
)
from ai.backend.manager.services.user.actions.get_user import GetUserAction


@strawberry.field(
    description=(
        "Added in 26.2.0. Get a single user by UUID (admin only). "
        "Requires superadmin privileges. Returns an error if user is not found."
    )
)  # type: ignore[misc]
async def admin_user_v2(
    info: Info[StrawberryGQLContext],
    user_id: UUID,
) -> UserV2GQL | None:
    """Get a single user by UUID.

    Args:
        info: Strawberry GraphQL context.
        user_id: UUID of the user to retrieve.

    Returns:
        UserV2GQL object.

    Raises:
        UserNotFound: If the user with the given UUID does not exist.
    """
    processors = info.context.processors

    # Execute GetUserAction via processor
    action_result = await processors.user.get_user.wait_for_complete(
        GetUserAction(user_uuid=user_id)
    )

    return UserV2GQL.from_data(action_result.user)


@strawberry.field(
    description=(
        "Added in 26.2.0. List all users with filtering and pagination (admin only). "
        "Requires superadmin privileges."
    )
)  # type: ignore[misc]
async def admin_users_v2(
    info: Info[StrawberryGQLContext],
    filter: UserFilterGQL | None = None,
    order_by: list[UserOrderByGQL] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> UserV2Connection | None:
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
async def domain_users_v2(
    info: Info[StrawberryGQLContext],
    scope: DomainUserScopeGQL,
    filter: UserFilterGQL | None = None,
    order_by: list[UserOrderByGQL] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> UserV2Connection | None:
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
    from ai.backend.manager.repositories.user.types import DomainUserSearchScope

    return await fetch_domain_users(
        info,
        scope=DomainUserSearchScope(domain_name=scope.domain_name),
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
async def project_users_v2(
    info: Info[StrawberryGQLContext],
    scope: ProjectUserScopeGQL,
    filter: UserFilterGQL | None = None,
    order_by: list[UserOrderByGQL] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> UserV2Connection | None:
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
    from ai.backend.manager.repositories.user.types import ProjectUserSearchScope

    return await fetch_project_users(
        info,
        scope=ProjectUserSearchScope(project_id=scope.project_id),
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
async def my_user_v2(
    info: Info[StrawberryGQLContext],
) -> UserV2GQL | None:
    """Get the current authenticated user's information.

    Args:
        info: Strawberry GraphQL context.

    Returns:
        UserV2GQL for the current user.

    Raises:
        Unauthorized: If the user is not authenticated.
        UserNotFound: If the current user does not exist.
    """
    # Get current authenticated user
    me = current_user()
    if me is None:
        from aiohttp import web

        raise web.HTTPUnauthorized(reason="Authentication required")

    processors = info.context.processors

    # Execute GetUserAction via processor
    action_result = await processors.user.get_user.wait_for_complete(
        GetUserAction(user_uuid=me.user_id)
    )

    return UserV2GQL.from_data(action_result.user)
