"""Entity GQL query resolvers."""

from __future__ import annotations

from strawberry import Info

from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_root_field,
)
from ai.backend.manager.api.gql.entity.types import EntityTypeGQL
from ai.backend.manager.api.gql.types import StrawberryGQLContext


@gql_root_field(
    BackendAIGQLMeta(
        description=(
            "Every entity type the manager has operations wired for, in name order. "
            "What a field taking an entity type may be given is what this lists."
        ),
        added_version=NEXT_RELEASE_VERSION,
    )
)  # type: ignore[misc]
async def entity_types(
    info: Info[StrawberryGQLContext],
) -> list[EntityTypeGQL]:
    payload = info.context.adapters.entity.list_entity_types()
    return [EntityTypeGQL.from_pydantic(item, id_field="name") for item in payload.items]
