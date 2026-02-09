"""User V2 GraphQL data fetcher functions."""

from __future__ import annotations

from functools import lru_cache
from uuid import UUID

from strawberry import Info
from strawberry.relay import PageInfo

from ai.backend.manager.api.gql.adapter import PaginationOptions, PaginationSpec
from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.user_v2.types import (
    UserV2Connection,
    UserV2Edge,
    UserV2Filter,
    UserV2GQL,
    UserV2OrderBy,
)
from ai.backend.manager.models.user.row import UserRow
from ai.backend.manager.repositories.user.options import UserConditions, UserOrders
from ai.backend.manager.repositories.user.types import (
    DomainUserSearchScope,
    ProjectUserSearchScope,
)
from ai.backend.manager.services.user.actions.get_user import GetUserAction
from ai.backend.manager.services.user.actions.search_users import SearchUsersAction
from ai.backend.manager.services.user.actions.search_users_by_domain import (
    SearchUsersByDomainAction,
)
from ai.backend.manager.services.user.actions.search_users_by_project import (
    SearchUsersByProjectAction,
)


@lru_cache(maxsize=1)
def get_user_pagination_spec() -> PaginationSpec:
    """Cached pagination spec for user queries."""
    return PaginationSpec(
        forward_order=UserOrders.created_at(ascending=False),
        backward_order=UserOrders.created_at(ascending=True),
        forward_condition_factory=UserConditions.by_cursor_forward,
        backward_condition_factory=UserConditions.by_cursor_backward,
        tiebreaker_order=UserRow.uuid.asc(),
    )


async def fetch_user(
    info: Info[StrawberryGQLContext],
    user_uuid: UUID,
) -> UserV2GQL:
    """Fetch a single user by UUID.

    Args:
        info: Strawberry GraphQL context.
        user_uuid: UUID of the user to retrieve.

    Returns:
        UserV2GQL object.

    Raises:
        UserNotFound: If the user does not exist.
    """
    processors = info.context.processors

    action_result = await processors.user.get_user.wait_for_complete(
        GetUserAction(user_uuid=user_uuid)
    )

    return UserV2GQL.from_data(action_result.user)


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
        get_user_pagination_spec(),
        filter=filter,
        order_by=order_by,
        base_conditions=None,
    )

    # Execute via processor
    action_result = await processors.user.search_users.wait_for_complete(
        SearchUsersAction(querier=querier)
    )

    # Build connection
    nodes = [UserV2GQL.from_data(data) for data in action_result.users]
    edges = [UserV2Edge(node=node, cursor=encode_cursor(str(node.id))) for node in nodes]

    return UserV2Connection(
        edges=edges,
        page_info=PageInfo(
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=action_result.total_count,
    )


async def fetch_domain_users(
    info: Info[StrawberryGQLContext],
    scope: DomainUserSearchScope,
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
        get_user_pagination_spec(),
        filter=filter,
        order_by=order_by,
        base_conditions=None,
    )

    # Execute via processor with domain scope
    action_result = await processors.user.search_users_by_domain.wait_for_complete(
        SearchUsersByDomainAction(scope=scope, querier=querier)
    )

    # Build connection
    nodes = [UserV2GQL.from_data(data) for data in action_result.users]
    edges = [UserV2Edge(node=node, cursor=encode_cursor(str(node.id))) for node in nodes]

    return UserV2Connection(
        edges=edges,
        page_info=PageInfo(
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=action_result.total_count,
    )


async def fetch_project_users(
    info: Info[StrawberryGQLContext],
    scope: ProjectUserSearchScope,
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
        get_user_pagination_spec(),
        filter=filter,
        order_by=order_by,
        base_conditions=None,
    )

    # Execute via processor with project scope
    action_result = await processors.user.search_users_by_project.wait_for_complete(
        SearchUsersByProjectAction(scope=scope, querier=querier)
    )

    # Build connection
    nodes = [UserV2GQL.from_data(data) for data in action_result.users]
    edges = [UserV2Edge(node=node, cursor=encode_cursor(str(node.id))) for node in nodes]

    return UserV2Connection(
        edges=edges,
        page_info=PageInfo(
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=action_result.total_count,
    )
