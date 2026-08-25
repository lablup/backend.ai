from __future__ import annotations

from uuid import UUID

from strawberry import Info
from strawberry.relay import PageInfo

from ai.backend.common.data.entity.client_ip_masking import ClientIPMaskingPolicyID
from ai.backend.common.dto.manager.v2.client_ip_masking.request import (
    AdminSearchClientIPMaskingPoliciesInput,
    ClientIPMaskingPolicyOrder,
)
from ai.backend.common.dto.manager.v2.client_ip_masking.types import (
    ClientIPMaskingPolicyOrderField,
)
from ai.backend.common.dto.manager.v2.common import OrderDirection
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.api.gql.client_ip_masking.types import (
    ClientIPMaskingPolicyConnectionGQL,
    ClientIPMaskingPolicyEdgeGQL,
    ClientIPMaskingPolicyFilterGQL,
    ClientIPMaskingPolicyGQL,
    ClientIPMaskingPolicyOrderByGQL,
    ClientIPMaskingPolicyPayloadGQL,
    UpsertClientIPMaskingPolicyInputGQL,
)
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_mutation,
    gql_root_field,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Read the client IP masking set for every target (superadmin only).",
    )
)  # type: ignore[misc]
async def admin_client_ip_masking_policies(
    info: Info[StrawberryGQLContext],
    filter: ClientIPMaskingPolicyFilterGQL | None = None,
    order_by: list[ClientIPMaskingPolicyOrderByGQL] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> ClientIPMaskingPolicyConnectionGQL | None:
    check_admin_only()
    orders: list[ClientIPMaskingPolicyOrder] | None = None
    if order_by:
        orders = [
            ClientIPMaskingPolicyOrder(
                field=ClientIPMaskingPolicyOrderField(o.field.value),
                direction=OrderDirection(o.direction),
            )
            for o in order_by
        ]
    payload = await info.context.adapters.client_ip_masking.admin_search(
        AdminSearchClientIPMaskingPoliciesInput(
            filter=filter.to_pydantic() if filter else None,
            order=orders,
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        )
    )
    nodes = [ClientIPMaskingPolicyGQL.from_pydantic(item) for item in payload.items]
    edges = [
        ClientIPMaskingPolicyEdgeGQL(node=node, cursor=encode_cursor(node.id)) for node in nodes
    ]
    return ClientIPMaskingPolicyConnectionGQL(
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
        description="Set the client IP masking one target gets (superadmin only).",
    )
)
async def admin_upsert_client_ip_masking_policy(
    info: Info[StrawberryGQLContext],
    input: UpsertClientIPMaskingPolicyInputGQL,
) -> ClientIPMaskingPolicyPayloadGQL | None:
    check_admin_only()
    payload = await info.context.adapters.client_ip_masking.admin_upsert(input.to_pydantic())
    return ClientIPMaskingPolicyPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Drop one target's client IP masking policy so it falls back to the "
            "default (superadmin only)."
        ),
    )
)
async def admin_purge_client_ip_masking_policy(
    info: Info[StrawberryGQLContext],
    id: UUID,
) -> ClientIPMaskingPolicyPayloadGQL | None:
    check_admin_only()
    payload = await info.context.adapters.client_ip_masking.admin_purge(ClientIPMaskingPolicyID(id))
    return ClientIPMaskingPolicyPayloadGQL.from_pydantic(payload)
