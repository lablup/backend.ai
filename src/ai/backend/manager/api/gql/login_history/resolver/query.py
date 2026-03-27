"""LoginHistory GraphQL query resolvers."""

from __future__ import annotations

import strawberry
from strawberry import Info

from ai.backend.common.dto.manager.v2.login_history.request import (
    AdminSearchLoginHistoryInput,
    MySearchLoginHistoryInput,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_root_field,
)
from ai.backend.manager.api.gql.login_history.types import (
    LoginHistoryFilterGQL,
    LoginHistoryOrderByGQL,
    LoginHistoryV2ConnectionGQL,
    LoginHistoryV2EdgeGQL,
    LoginHistoryV2GQL,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Query login history with pagination and filtering. (admin only)",
    )
)  # type: ignore[misc]
async def admin_login_history_v2(
    info: Info[StrawberryGQLContext],
    filter: LoginHistoryFilterGQL | None = None,
    order_by: list[LoginHistoryOrderByGQL] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> LoginHistoryV2ConnectionGQL:
    check_admin_only()
    result = await info.context.adapters.login_history.admin_search(
        AdminSearchLoginHistoryInput(
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
    nodes = [LoginHistoryV2GQL.from_pydantic(item) for item in result.items]
    edges = [LoginHistoryV2EdgeGQL(node=node, cursor=encode_cursor(node.id)) for node in nodes]
    return LoginHistoryV2ConnectionGQL(
        edges=edges,
        page_info=strawberry.relay.PageInfo(
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=result.total_count,
    )


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Query login history of the current user with pagination and filtering.",
    )
)  # type: ignore[misc]
async def my_login_history_v2(
    info: Info[StrawberryGQLContext],
    filter: LoginHistoryFilterGQL | None = None,
    order_by: list[LoginHistoryOrderByGQL] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> LoginHistoryV2ConnectionGQL:
    result = await info.context.adapters.login_history.my_search(
        MySearchLoginHistoryInput(
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
    nodes = [LoginHistoryV2GQL.from_pydantic(item) for item in result.items]
    edges = [LoginHistoryV2EdgeGQL(node=node, cursor=encode_cursor(node.id)) for node in nodes]
    return LoginHistoryV2ConnectionGQL(
        edges=edges,
        page_info=strawberry.relay.PageInfo(
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=result.total_count,
    )
