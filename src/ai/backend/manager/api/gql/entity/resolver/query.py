"""Entity GQL query resolvers."""

from __future__ import annotations

from strawberry import Info

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
        added_version="26.9.0",
    )
)  # type: ignore[misc]
async def entity_types(
    info: Info[StrawberryGQLContext],
) -> list[EntityTypeGQL]:
    payload = info.context.adapters.entity.list_entity_types()
    return [EntityTypeGQL.from_pydantic(item, id_field="name") for item in payload.items]
