"""Project Fair Share fetcher functions."""

from __future__ import annotations

from uuid import UUID

from strawberry import Info
from strawberry.relay import PageInfo

from ai.backend.common.dto.manager.v2.fair_share.request import (
    GetProjectFairShareInput,
    SearchProjectFairSharesInput,
)
from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.api.gql.fair_share.types import (
    ProjectFairShareConnection,
    ProjectFairShareEdge,
    ProjectFairShareFilter,
    ProjectFairShareGQL,
    ProjectFairShareOrderBy,
    RGProjectFairShareFilter,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.repositories.fair_share.types import ProjectFairShareSearchScope


async def fetch_project_fair_shares(
    info: Info[StrawberryGQLContext],
    filter: ProjectFairShareFilter | None = None,
    order_by: list[ProjectFairShareOrderBy] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> ProjectFairShareConnection:
    """Fetch project fair shares with optional filtering, ordering, and pagination.

    Args:
        info: GraphQL context info
        filter: Optional filter criteria
        order_by: Optional ordering specification
        before/after/first/last: Cursor-based pagination parameters
        limit/offset: Offset-based pagination parameters
    """
    pydantic_filter = filter.to_pydantic() if filter else None
    pydantic_orders = [o.to_pydantic() for o in order_by] if order_by else None

    payload = await info.context.adapters.fair_share.search_project(
        SearchProjectFairSharesInput(
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

    nodes = [ProjectFairShareGQL.from_node(item) for item in payload.items]
    edges = [ProjectFairShareEdge(node=node, cursor=encode_cursor(str(node.id))) for node in nodes]

    return ProjectFairShareConnection(
        edges=edges,
        page_info=PageInfo(
            has_next_page=len(payload.items) > 0 and (first is not None or limit is not None),
            has_previous_page=(offset or 0) > 0 or last is not None,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=payload.total_count,
    )


async def fetch_rg_project_fair_shares(
    info: Info[StrawberryGQLContext],
    scope: ProjectFairShareSearchScope,
    filter: RGProjectFairShareFilter | None = None,
    order_by: list[ProjectFairShareOrderBy] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> ProjectFairShareConnection:
    """Fetch project fair shares using resource group scope.

    Returns all projects in the scope, including those without records (with defaults).
    """
    pydantic_filter = filter.to_pydantic() if filter else None
    pydantic_orders = [o.to_pydantic() for o in order_by] if order_by else None

    payload = await info.context.adapters.fair_share.search_rg_project(
        SearchProjectFairSharesInput(
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
        domain_name=scope.domain_name,
    )

    nodes = [ProjectFairShareGQL.from_node(item) for item in payload.items]
    edges = [ProjectFairShareEdge(node=node, cursor=encode_cursor(str(node.id))) for node in nodes]

    return ProjectFairShareConnection(
        edges=edges,
        page_info=PageInfo(
            has_next_page=len(payload.items) > 0 and (first is not None or limit is not None),
            has_previous_page=(offset or 0) > 0 or last is not None,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=payload.total_count,
    )


async def fetch_single_project_fair_share(
    info: Info[StrawberryGQLContext],
    resource_group_name: str,
    project_id: UUID,
) -> ProjectFairShareGQL:
    """Fetch a single project fair share record.

    Returns the fair share record for the specified project and resource group.
    If no record exists, returns a default-generated object (adapter handles defaults).
    """
    payload = await info.context.adapters.fair_share.get_project(
        GetProjectFairShareInput(
            resource_group=resource_group_name,
            project_id=project_id,
        )
    )

    return ProjectFairShareGQL.from_node(payload.item)  # type: ignore[arg-type]
