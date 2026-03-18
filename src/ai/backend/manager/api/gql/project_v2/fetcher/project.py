"""Project V2 GraphQL data fetcher functions."""

from __future__ import annotations

from functools import lru_cache
from uuid import UUID

from strawberry import Info
from strawberry.relay import PageInfo

from ai.backend.manager.api.gql.adapter import PaginationOptions, PaginationSpec
from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.api.gql.domain_v2.fetcher import fetch_domain
from ai.backend.manager.api.gql.domain_v2.types import DomainV2GQL
from ai.backend.manager.api.gql.project_v2.types import (
    ProjectV2Connection,
    ProjectV2Edge,
    ProjectV2Filter,
    ProjectV2GQL,
    ProjectV2OrderBy,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.models.group.row import GroupRow
from ai.backend.manager.repositories.base import QueryCondition
from ai.backend.manager.repositories.group.options import GroupConditions, GroupOrders
from ai.backend.manager.repositories.group.types import (
    DomainProjectSearchScope,
    UserProjectSearchScope,
)
from ai.backend.manager.services.group.actions.search_projects import (
    GetProjectAction,
    SearchProjectsAction,
    SearchProjectsByDomainAction,
    SearchProjectsByUserAction,
)


@lru_cache(maxsize=1)
def get_project_pagination_spec() -> PaginationSpec:
    """Cached pagination spec for project queries."""

    def forward_cursor_factory(cursor_id: str) -> QueryCondition:
        """Convert string cursor to UUID for GroupConditions."""
        return GroupConditions.by_cursor_forward(UUID(cursor_id))

    def backward_cursor_factory(cursor_id: str) -> QueryCondition:
        """Convert string cursor to UUID for GroupConditions."""
        return GroupConditions.by_cursor_backward(UUID(cursor_id))

    return PaginationSpec(
        forward_order=GroupOrders.created_at(ascending=False),
        backward_order=GroupOrders.created_at(ascending=True),
        forward_condition_factory=forward_cursor_factory,
        backward_condition_factory=backward_cursor_factory,
        tiebreaker_order=GroupRow.id.asc(),
    )


async def fetch_project(
    info: Info[StrawberryGQLContext],
    project_id: UUID,
) -> ProjectV2GQL:
    """Fetch a single project by ID.

    Args:
        info: Strawberry GraphQL context.
        project_id: UUID of the project to retrieve.

    Returns:
        ProjectV2GQL object.

    Raises:
        ProjectNotFound: If the project does not exist.
    """
    processors = info.context.processors

    # Execute via processor
    action_result = await processors.group.get_project.wait_for_complete(
        GetProjectAction(project_id=project_id)
    )

    return ProjectV2GQL.from_data(action_result.data)


async def fetch_admin_projects(
    info: Info[StrawberryGQLContext],
    filter: ProjectV2Filter | None = None,
    order_by: list[ProjectV2OrderBy] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> ProjectV2Connection:
    """Fetch all projects with optional filtering, ordering, and pagination.

    This is the admin-level fetcher that returns all projects in the system.

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
        get_project_pagination_spec(),
        filter=filter,
        order_by=order_by,
        base_conditions=None,
    )

    # Execute via processor
    action_result = await processors.group.search_projects.wait_for_complete(
        SearchProjectsAction(querier=querier)
    )

    # Build connection
    nodes = [ProjectV2GQL.from_data(data) for data in action_result.items]
    edges = [ProjectV2Edge(node=node, cursor=encode_cursor(str(node.id))) for node in nodes]

    return ProjectV2Connection(
        edges=edges,
        page_info=PageInfo(
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=action_result.total_count,
    )


async def fetch_domain_projects(
    info: Info[StrawberryGQLContext],
    scope: DomainProjectSearchScope,
    filter: ProjectV2Filter | None = None,
    order_by: list[ProjectV2OrderBy] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> ProjectV2Connection:
    """Fetch projects within a specific domain.

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
        get_project_pagination_spec(),
        filter=filter,
        order_by=order_by,
        base_conditions=None,
    )

    # Execute via processor with domain scope
    action_result = await processors.group.search_projects_by_domain.wait_for_complete(
        SearchProjectsByDomainAction(scope=scope, querier=querier)
    )

    # Build connection
    nodes = [ProjectV2GQL.from_data(data) for data in action_result.items]
    edges = [ProjectV2Edge(node=node, cursor=encode_cursor(str(node.id))) for node in nodes]

    return ProjectV2Connection(
        edges=edges,
        page_info=PageInfo(
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=action_result.total_count,
    )


async def fetch_user_projects(
    info: Info[StrawberryGQLContext],
    scope: UserProjectSearchScope,
    filter: ProjectV2Filter | None = None,
    order_by: list[ProjectV2OrderBy] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> ProjectV2Connection:
    """Fetch projects that a specific user is a member of.

    Args:
        info: Strawberry GraphQL context.
        scope: User scope specifying which user to query projects for.
        filter: Optional additional filter criteria.
        order_by: Optional ordering specification.
        before: Cursor for backward pagination.
        after: Cursor for forward pagination.
        first: Number of items from the start.
        last: Number of items from the end.
        limit: Maximum number of items (offset-based).
        offset: Starting position (offset-based).

    Returns:
        ProjectV2Connection with paginated project records for the user.
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
        get_project_pagination_spec(),
        filter=filter,
        order_by=order_by,
        base_conditions=None,
    )

    # Execute via processor with user scope
    action_result = await processors.group.search_projects_by_user.wait_for_complete(
        SearchProjectsByUserAction(scope=scope, querier=querier)
    )

    # Build connection
    nodes = [ProjectV2GQL.from_data(data) for data in action_result.items]
    edges = [ProjectV2Edge(node=node, cursor=encode_cursor(str(node.id))) for node in nodes]

    return ProjectV2Connection(
        edges=edges,
        page_info=PageInfo(
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=action_result.total_count,
    )


async def fetch_project_domain(
    info: Info[StrawberryGQLContext],
    project_id: UUID,
) -> DomainV2GQL:
    """Fetch the domain that a project belongs to.

    Args:
        info: Strawberry GraphQL context.
        project_id: UUID of the project.

    Returns:
        DomainV2GQL object for the project's domain.

    Raises:
        ProjectNotFound: If the project does not exist.
        DomainNotFound: If the project's domain does not exist.
    """
    # Get the project to find its domain_name
    processors = info.context.processors
    action_result = await processors.group.get_project.wait_for_complete(
        GetProjectAction(project_id=project_id)
    )

    # Fetch domain by name
    return await fetch_domain(info, domain_name=action_result.data.domain_name)
