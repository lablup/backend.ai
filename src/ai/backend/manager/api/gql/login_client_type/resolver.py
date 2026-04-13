"""GraphQL query and mutation resolvers for login client types."""

from __future__ import annotations

from uuid import UUID

from strawberry import Info
from strawberry.relay import PageInfo

from ai.backend.common.dto.manager.v2.login_client_type.request import (
    SearchLoginClientTypesInput,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_mutation,
    gql_root_field,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only

from .types import (
    CreateLoginClientTypeInputGQL,
    CreateLoginClientTypePayloadGQL,
    DeleteLoginClientTypePayloadGQL,
    LoginClientTypeConnection,
    LoginClientTypeEdge,
    LoginClientTypeFilterGQL,
    LoginClientTypeGQL,
    LoginClientTypeOrderByGQL,
    UpdateLoginClientTypeInputGQL,
    UpdateLoginClientTypePayloadGQL,
)


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Get a single login client type by id.",
    )
)  # type: ignore[misc]
async def login_client_type(
    info: Info[StrawberryGQLContext],
    id: UUID,
) -> LoginClientTypeGQL | None:
    node = await info.context.adapters.login_client_type.get(id)
    return LoginClientTypeGQL.from_pydantic(node)


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=("Search login client types with filtering, ordering, and pagination."),
    )
)  # type: ignore[misc]
async def login_client_types(
    info: Info[StrawberryGQLContext],
    filter: LoginClientTypeFilterGQL | None = None,
    order_by: list[LoginClientTypeOrderByGQL] | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> LoginClientTypeConnection | None:
    pydantic_filter = filter.to_pydantic() if filter else None
    pydantic_order = [o.to_pydantic() for o in order_by] if order_by else None

    payload = await info.context.adapters.login_client_type.search(
        SearchLoginClientTypesInput(
            filter=pydantic_filter,
            order=pydantic_order,
            limit=limit if limit is not None else 50,
            offset=offset if offset is not None else 0,
        )
    )

    nodes = [LoginClientTypeGQL.from_pydantic(node) for node in payload.items]
    edges = [LoginClientTypeEdge(node=node, cursor=encode_cursor(str(node.id))) for node in nodes]

    return LoginClientTypeConnection(
        edges=edges,
        page_info=PageInfo(
            has_next_page=payload.has_next_page,
            has_previous_page=payload.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=payload.total_count,
    )


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Create a new login client type (super admin only).",
    )
)  # type: ignore[misc]
async def admin_create_login_client_type(
    info: Info[StrawberryGQLContext],
    input: CreateLoginClientTypeInputGQL,
) -> CreateLoginClientTypePayloadGQL:
    check_admin_only()
    payload = await info.context.adapters.login_client_type.admin_create(input.to_pydantic())
    return CreateLoginClientTypePayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Update a login client type (super admin only).",
    )
)  # type: ignore[misc]
async def admin_update_login_client_type(
    info: Info[StrawberryGQLContext],
    id: UUID,
    input: UpdateLoginClientTypeInputGQL,
) -> UpdateLoginClientTypePayloadGQL:
    check_admin_only()
    payload = await info.context.adapters.login_client_type.admin_update(id, input.to_pydantic())
    return UpdateLoginClientTypePayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Delete a login client type (super admin only).",
    )
)  # type: ignore[misc]
async def admin_delete_login_client_type(
    info: Info[StrawberryGQLContext],
    id: UUID,
) -> DeleteLoginClientTypePayloadGQL:
    check_admin_only()
    payload = await info.context.adapters.login_client_type.admin_delete(id)
    return DeleteLoginClientTypePayloadGQL.from_pydantic(payload)
