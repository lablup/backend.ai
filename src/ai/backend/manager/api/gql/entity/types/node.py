"""Entity type GQL node."""

from __future__ import annotations

from collections.abc import Iterable
from typing import override

from strawberry import Info
from strawberry.relay import NodeID

from ai.backend.common.dto.manager.v2.entity.response import EntityTypeNode
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_field,
    gql_node_type,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin
from ai.backend.manager.api.gql.types import StrawberryGQLContext

__all__ = ("EntityTypeGQL",)


@gql_node_type(
    BackendAIGQLMeta(
        description=(
            "One entity type the manager has operations wired for. An entity type is "
            "declared where its operations are wired, not as a fixed enum, so this is "
            "what a request may name."
        ),
        added_version="26.9.0",
    ),
    name="EntityType",
)
class EntityTypeGQL(PydanticNodeMixin[EntityTypeNode]):
    id: NodeID[str] = gql_field(description="The entity type, which is its own id.")
    name: str = gql_field(description="The entity type, as a request names it.")

    @classmethod
    @override
    async def resolve_nodes(  # type: ignore[override]  # Strawberry Node uses AwaitableOrValue overloads incompatible with async def
        cls,
        *,
        info: Info[StrawberryGQLContext],
        node_ids: Iterable[str],
        required: bool = False,
    ) -> Iterable[EntityTypeGQL | None]:
        payload = info.context.adapters.entity.list_entity_types()
        by_name = {item.name: item for item in payload.items}
        return [
            EntityTypeGQL.from_pydantic(by_name[nid], id_field="name") if nid in by_name else None
            for nid in node_ids
        ]
