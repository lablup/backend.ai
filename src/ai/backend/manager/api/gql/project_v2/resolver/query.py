"""Project V2 GraphQL query resolvers."""

from __future__ import annotations

from uuid import UUID

import strawberry
from strawberry import Info
from strawberry.relay import PageInfo

from ai.backend.common.dto.manager.v2.group.request import AdminSearchGroupsInput
from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.api.gql.domain_v2.types import DomainV2GQL
from ai.backend.manager.api.gql.project_v2.types import (
    DomainProjectScope,
    ProjectV2Connection,
    ProjectV2Filter,
    ProjectV2GQL,
    ProjectV2OrderBy,
)
from ai.backend.manager.api.gql.project_v2.types.node import ProjectV2Edge
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only
from ai.backend.manager.services.group.actions.search_projects import GetProjectAction


@strawberry.field(
    description=(
        "Added in 26.2.0. Get a single project by ID. Returns an error if project is not found."
    )
)  # type: ignore[misc]
async def project_v2(
    info: Info[StrawberryGQLContext],
    project_id: UUID,
) -> ProjectV2GQL | None:
    """Get a single project by UUID."""
    action_result = await info.context.processors.group.get_project.wait_for_complete(
        GetProjectAction(project_id=project_id)
    )
    return ProjectV2GQL.from_data(action_result.data)


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
    """List all projects with optional filtering, ordering, and pagination."""
    check_admin_only()
    payload = await info.context.adapters.project.admin_search(
        AdminSearchGroupsInput(
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
    nodes = [ProjectV2GQL.from_node(node) for node in payload.items]
    edges = [ProjectV2Edge(node=node, cursor=encode_cursor(str(node.id))) for node in nodes]
    return ProjectV2Connection(
        edges=edges,
        page_info=PageInfo(
            has_next_page=payload.has_next_page,
            has_previous_page=payload.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=payload.total_count,
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
    """List projects within a specific domain."""
    from ai.backend.manager.repositories.group.types import DomainProjectSearchScope

    repo_scope = DomainProjectSearchScope(domain_name=scope.domain_name)
    payload = await info.context.adapters.project.search_by_domain(
        scope=repo_scope,
        input=AdminSearchGroupsInput(
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
    nodes = [ProjectV2GQL.from_node(node) for node in payload.items]
    edges = [ProjectV2Edge(node=node, cursor=encode_cursor(str(node.id))) for node in nodes]
    return ProjectV2Connection(
        edges=edges,
        page_info=PageInfo(
            has_next_page=payload.has_next_page,
            has_previous_page=payload.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=payload.total_count,
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
    """Get the domain that a project belongs to."""
    from ai.backend.manager.services.domain.actions.get_domain import GetDomainAction

    action_result = await info.context.processors.group.get_project.wait_for_complete(
        GetProjectAction(project_id=project_id)
    )
    domain_result = await info.context.processors.domain.get_domain.wait_for_complete(
        GetDomainAction(domain_name=action_result.data.domain_name)
    )
    return DomainV2GQL.from_data(domain_result.data)
