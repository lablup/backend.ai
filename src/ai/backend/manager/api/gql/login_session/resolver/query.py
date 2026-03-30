"""LoginSession GraphQL query and mutation resolvers."""

from __future__ import annotations

from uuid import UUID

import strawberry
from strawberry import Info

from ai.backend.common.dto.manager.v2.login_session.request import (
    AdminRevokeLoginSessionInput,
    AdminSearchLoginSessionsInput,
    MyRevokeLoginSessionInput,
    MySearchLoginSessionsInput,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_mutation,
    gql_root_field,
)
from ai.backend.manager.api.gql.login_session.types import (
    LoginSessionFilterGQL,
    LoginSessionOrderByGQL,
    LoginSessionV2ConnectionGQL,
    LoginSessionV2EdgeGQL,
    LoginSessionV2GQL,
    RevokeLoginSessionPayloadGQL,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Query login sessions with pagination and filtering. (admin only)",
    )
)  # type: ignore[misc]
async def admin_login_sessions_v2(
    info: Info[StrawberryGQLContext],
    filter: LoginSessionFilterGQL | None = None,
    order_by: list[LoginSessionOrderByGQL] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> LoginSessionV2ConnectionGQL:
    check_admin_only()
    result = await info.context.adapters.login_session.admin_search(
        AdminSearchLoginSessionsInput(
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
    nodes = [LoginSessionV2GQL.from_pydantic(item) for item in result.items]
    edges = [LoginSessionV2EdgeGQL(node=node, cursor=encode_cursor(node.id)) for node in nodes]
    return LoginSessionV2ConnectionGQL(
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
        description="Query login sessions of the current user with pagination and filtering.",
    )
)  # type: ignore[misc]
async def my_login_sessions_v2(
    info: Info[StrawberryGQLContext],
    filter: LoginSessionFilterGQL | None = None,
    order_by: list[LoginSessionOrderByGQL] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> LoginSessionV2ConnectionGQL:
    result = await info.context.adapters.login_session.my_search(
        MySearchLoginSessionsInput(
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
    nodes = [LoginSessionV2GQL.from_pydantic(item) for item in result.items]
    edges = [LoginSessionV2EdgeGQL(node=node, cursor=encode_cursor(node.id)) for node in nodes]
    return LoginSessionV2ConnectionGQL(
        edges=edges,
        page_info=strawberry.relay.PageInfo(
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=result.total_count,
    )


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Revoke a login session. (admin only)",
    )
)  # type: ignore[misc]
async def admin_revoke_login_session(
    info: Info[StrawberryGQLContext],
    session_id: UUID,
) -> RevokeLoginSessionPayloadGQL:
    check_admin_only()
    payload = await info.context.adapters.login_session.admin_revoke(
        AdminRevokeLoginSessionInput(session_id=session_id)
    )
    return RevokeLoginSessionPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Revoke a login session owned by the current user.",
    )
)  # type: ignore[misc]
async def my_revoke_login_session(
    info: Info[StrawberryGQLContext],
    session_id: UUID,
) -> RevokeLoginSessionPayloadGQL:
    payload = await info.context.adapters.login_session.my_revoke(
        MyRevokeLoginSessionInput(session_id=session_id)
    )
    return RevokeLoginSessionPayloadGQL.from_pydantic(payload)
