"""Entity type GQL node."""

from __future__ import annotations

from strawberry.relay import NodeID

from ai.backend.common.dto.manager.v2.entity.response import EntityTypeNode
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_field,
    gql_node_type,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin

__all__ = ("EntityTypeGQL",)


@gql_node_type(
    BackendAIGQLMeta(
        description=(
            "One entity type the manager has operations wired for. An entity type is "
            "declared where its operations are wired, not as a fixed enum, so this is "
            "what a request may name."
        ),
        added_version=NEXT_RELEASE_VERSION,
    ),
    name="EntityType",
)
class EntityTypeGQL(PydanticNodeMixin[EntityTypeNode]):
    id: NodeID[str] = gql_field(description="The entity type, which is its own id.")
    name: str = gql_field(description="The entity type, as a request names it.")
