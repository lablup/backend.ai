"""User GraphQL query resolvers."""

from __future__ import annotations

from uuid import UUID

import strawberry
from strawberry import Info
from strawberry.relay import PageInfo

from ai.backend.common.contexts.user import current_user
from ai.backend.common.dto.manager.v2.user.request import AdminSearchUsersInput
from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.user.types import (
    DomainUserScopeGQL,
    ProjectUserScopeGQL,
    UserFilterGQL,
    UserOrderByGQL,
    UserV2Connection,
    UserV2Edge,
    UserV2GQL,
)
from ai.backend.manager.api.gql.utils import check_admin_only
from ai.backend.manager.repositories.user.types import (
    DomainUserSearchScope,
    ProjectUserSearchScope,
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
) -> UserV2GQL | None:
    check_admin_only()
    payload = await info.context.adapters.user.get(user_id)
    return UserV2GQL.from_pydantic(payload.user)


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
    check_admin_only()
    payload = await info.context.adapters.user.gql_admin_search(
        input=AdminSearchUsersInput(
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
    nodes = [UserV2GQL.from_pydantic(item) for item in payload.items]
    edges = [UserV2Edge(node=node, cursor=encode_cursor(str(node.id))) for node in nodes]
    return UserV2Connection(
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
    payload = await info.context.adapters.user.gql_search_by_domain(
        scope=DomainUserSearchScope(domain_name=scope.domain_name),
        input=AdminSearchUsersInput(
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
    nodes = [UserV2GQL.from_pydantic(item) for item in payload.items]
    edges = [UserV2Edge(node=node, cursor=encode_cursor(str(node.id))) for node in nodes]
    return UserV2Connection(
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
    payload = await info.context.adapters.user.gql_search_by_project(
        scope=ProjectUserSearchScope(project_id=scope.project_id),
        input=AdminSearchUsersInput(
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
    nodes = [UserV2GQL.from_pydantic(item) for item in payload.items]
    edges = [UserV2Edge(node=node, cursor=encode_cursor(str(node.id))) for node in nodes]
    return UserV2Connection(
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
        "Added in 26.2.0. Get the current authenticated user's information. "
        "Returns the user associated with the current session. "
        "Returns an error if not authenticated."
    )
)  # type: ignore[misc]
async def my_user_v2(
    info: Info[StrawberryGQLContext],
) -> UserV2GQL | None:
    me = current_user()
    if me is None:
        from aiohttp import web

        raise web.HTTPUnauthorized(reason="Authentication required")

    payload = await info.context.adapters.user.get(me.user_id)
    return UserV2GQL.from_pydantic(payload.user)
