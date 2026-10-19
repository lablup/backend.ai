"""GraphQL query and mutation resolvers for login client types."""

from __future__ import annotations

from uuid import UUID

from strawberry import Info
from strawberry.relay import PageInfo

from ai.backend.common.dto.manager.defs import DEFAULT_PAGE_LIMIT
from ai.backend.common.dto.manager.v2.login_client_type.request import (
    SearchLoginClientTypesInput,
)
from ai.backend.common.dto.manager.v2.login_client_type.response import (
    DeleteLoginClientTypePayload,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.base import encode_cursor, to_global_id
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
    PartialBulkLoginClientTypesPayloadGQL,
    PartialBulkPurgeLoginClientTypesInputGQL,
    PartialBulkUpdateLoginClientTypesInputGQL,
    PurgeLoginClientTypePayloadGQL,
    UpdateLoginClientTypeInputGQL,
    UpdateLoginClientTypePayloadGQL,
)


@gql_root_field(
    BackendAIGQLMeta(
        added_version="26.4.2",
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
        added_version="26.4.2",
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
            limit=limit if limit is not None else DEFAULT_PAGE_LIMIT,
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
        added_version="26.4.2",
        description="Create a new login client type (super admin only).",
    )
)
async def admin_create_login_client_type(
    info: Info[StrawberryGQLContext],
    input: CreateLoginClientTypeInputGQL,
) -> CreateLoginClientTypePayloadGQL | None:
    check_admin_only()
    payload = await info.context.adapters.login_client_type.admin_create(input.to_pydantic())
    return CreateLoginClientTypePayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Update a login client type. Only provided fields will be updated.",
    )
)
async def update_login_client_type(
    info: Info[StrawberryGQLContext],
    id: UUID,
    input: UpdateLoginClientTypeInputGQL,
) -> UpdateLoginClientTypePayloadGQL:
    payload = await info.context.adapters.login_client_type.update(id, input.to_pydantic())
    return UpdateLoginClientTypePayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Permanently remove a login client type.",
    )
)
async def purge_login_client_type(
    info: Info[StrawberryGQLContext],
    id: UUID,
) -> PurgeLoginClientTypePayloadGQL:
    payload = await info.context.adapters.login_client_type.purge(id)
    return PurgeLoginClientTypePayloadGQL.from_pydantic(
        payload, extra={"purged_id": to_global_id(LoginClientTypeGQL, payload.entity_id)}
    )


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Update several login client types, answering for each one.",
    )
)
async def partial_bulk_update_login_client_types(
    info: Info[StrawberryGQLContext],
    input: PartialBulkUpdateLoginClientTypesInputGQL,
) -> PartialBulkLoginClientTypesPayloadGQL:
    payload = await info.context.adapters.login_client_type.partial_bulk_update(input.to_pydantic())
    return PartialBulkLoginClientTypesPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Permanently remove several login client types, answering for each one.",
    )
)
async def partial_bulk_purge_login_client_types(
    info: Info[StrawberryGQLContext],
    input: PartialBulkPurgeLoginClientTypesInputGQL,
) -> PartialBulkLoginClientTypesPayloadGQL:
    payload = await info.context.adapters.login_client_type.partial_bulk_purge(input.to_pydantic())
    return PartialBulkLoginClientTypesPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Update a login client type (super admin only).",
    ),
    deprecation_reason=f"Deprecated since {NEXT_RELEASE_VERSION}. Use `updateLoginClientType`.",
)
async def admin_update_login_client_type(
    info: Info[StrawberryGQLContext],
    id: UUID,
    input: UpdateLoginClientTypeInputGQL,
) -> UpdateLoginClientTypePayloadGQL | None:
    check_admin_only()
    payload = await info.context.adapters.login_client_type.update(id, input.to_pydantic())
    return UpdateLoginClientTypePayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Delete a login client type (super admin only).",
    ),
    deprecation_reason=f"Deprecated since {NEXT_RELEASE_VERSION}. Use `purgeLoginClientType`.",
)
async def admin_delete_login_client_type(
    info: Info[StrawberryGQLContext],
    id: UUID,
) -> DeleteLoginClientTypePayloadGQL | None:
    check_admin_only()
    payload = await info.context.adapters.login_client_type.purge(id)
    return DeleteLoginClientTypePayloadGQL.from_pydantic(
        DeleteLoginClientTypePayload(id=payload.id, entity_id=payload.entity_id)
    )
