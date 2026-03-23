"""Keypair self-service GraphQL query resolvers."""

from __future__ import annotations

from strawberry import Info
from strawberry.relay import PageInfo

from ai.backend.common.dto.manager.v2.keypair.request import SearchMyKeypairsGQLInput
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_root_field,
)
from ai.backend.manager.api.gql.keypair.types.filters import KeypairFilterGQL, KeypairOrderByGQL
from ai.backend.manager.api.gql.keypair.types.node import KeyPairConnection, KeyPairEdge, KeyPairGQL
from ai.backend.manager.api.gql.types import StrawberryGQLContext


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="List keypairs owned by the current authenticated user. Supports filtering, ordering, and both cursor-based and offset-based pagination.",
    )
)  # type: ignore[misc]
async def my_keypairs(
    info: Info[StrawberryGQLContext],
    filter: KeypairFilterGQL | None = None,
    order_by: list[KeypairOrderByGQL] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> KeyPairConnection:
    result = await info.context.adapters.user.search_my_keypairs(
        SearchMyKeypairsGQLInput(
            filter=filter.to_pydantic() if filter is not None else None,
            order=[o.to_pydantic() for o in order_by] if order_by is not None else None,
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        ),
    )
    nodes = [KeyPairGQL.from_pydantic(item) for item in result.items]
    edges = [KeyPairEdge(node=node, cursor=encode_cursor(str(node.id))) for node in nodes]
    return KeyPairConnection(
        edges=edges,
        page_info=PageInfo(
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=result.total_count,
    )
