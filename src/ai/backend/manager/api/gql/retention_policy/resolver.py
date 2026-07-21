from __future__ import annotations

from uuid import UUID

from strawberry import Info
from strawberry.relay import PageInfo

from ai.backend.common.dto.manager.v2.common import OrderDirection
from ai.backend.common.dto.manager.v2.retention_policy.request import (
    RetentionPolicyFilter,
    RetentionPolicyOrder,
    SearchRetentionPoliciesInput,
)
from ai.backend.common.dto.manager.v2.retention_policy.types import RetentionPolicyOrderField
from ai.backend.common.identifier.retention_policy import RetentionPolicyID
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.decorators import BackendAIGQLMeta, gql_mutation, gql_root_field
from ai.backend.manager.api.gql.retention_policy.types import (
    CreateRetentionPolicyInputGQL,
    CreateRetentionPolicyPayloadGQL,
    DeleteRetentionPolicyPayloadGQL,
    PurgeRetentionPolicyPayloadGQL,
    RetentionPolicyConnection,
    RetentionPolicyEdge,
    RetentionPolicyFilterGQL,
    RetentionPolicyGQL,
    RetentionPolicyOrderByGQL,
    UpdateRetentionPolicyInputGQL,
    UpdateRetentionPolicyPayloadGQL,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Search retention policies (superadmin only).",
    )
)  # type: ignore[misc]
async def admin_retention_policies(
    info: Info[StrawberryGQLContext],
    filter: RetentionPolicyFilterGQL | None = None,
    order_by: list[RetentionPolicyOrderByGQL] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> RetentionPolicyConnection | None:
    check_admin_only()
    filter_dto: RetentionPolicyFilter | None = filter.to_pydantic() if filter else None
    orders_dto: list[RetentionPolicyOrder] | None = None
    if order_by:
        orders_dto = [
            RetentionPolicyOrder(
                field=RetentionPolicyOrderField(o.field.value),
                direction=OrderDirection(o.direction),
            )
            for o in order_by
        ]

    search_input = SearchRetentionPoliciesInput(
        filter=filter_dto,
        order=orders_dto,
        first=first,
        after=after,
        last=last,
        before=before,
        limit=limit,
        offset=offset,
    )

    result = await info.context.adapters.retention_policy.search(search_input)
    edges = [
        RetentionPolicyEdge(
            node=RetentionPolicyGQL.from_pydantic(item),
            cursor=str(item.id),
        )
        for item in result.items
    ]
    return RetentionPolicyConnection(
        edges=edges,
        page_info=PageInfo(
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
        description="Get a single retention policy by ID (superadmin only).",
    )
)  # type: ignore[misc]
async def admin_retention_policy(
    info: Info[StrawberryGQLContext],
    id: UUID,
) -> RetentionPolicyGQL | None:
    check_admin_only()
    node = await info.context.adapters.retention_policy.get(RetentionPolicyID(id))
    return RetentionPolicyGQL.from_pydantic(node)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Create a retention policy (superadmin only).",
    )
)
async def admin_create_retention_policy(
    info: Info[StrawberryGQLContext],
    input: CreateRetentionPolicyInputGQL,
) -> CreateRetentionPolicyPayloadGQL | None:
    check_admin_only()
    dto = input.to_pydantic()
    payload = await info.context.adapters.retention_policy.create(dto)
    return CreateRetentionPolicyPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Update a retention policy (superadmin only).",
    )
)
async def admin_update_retention_policy(
    info: Info[StrawberryGQLContext],
    input: UpdateRetentionPolicyInputGQL,
) -> UpdateRetentionPolicyPayloadGQL | None:
    check_admin_only()
    dto = input.to_pydantic()
    payload = await info.context.adapters.retention_policy.update(dto)
    return UpdateRetentionPolicyPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Delete a retention policy (superadmin only).",
    )
)
async def admin_delete_retention_policy(
    info: Info[StrawberryGQLContext],
    id: UUID,
) -> DeleteRetentionPolicyPayloadGQL | None:
    check_admin_only()
    payload = await info.context.adapters.retention_policy.delete(RetentionPolicyID(id))
    return DeleteRetentionPolicyPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Purge (permanently remove) a retention policy (superadmin only).",
    )
)
async def admin_purge_retention_policy(
    info: Info[StrawberryGQLContext],
    id: UUID,
) -> PurgeRetentionPolicyPayloadGQL | None:
    check_admin_only()
    payload = await info.context.adapters.retention_policy.purge(RetentionPolicyID(id))
    return PurgeRetentionPolicyPayloadGQL.from_pydantic(payload)
