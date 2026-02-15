"""GraphQL types for RBAC entity search."""

from __future__ import annotations

import strawberry

from ai.backend.manager.api.gql.rbac.types.entity_node import EntityNode


@strawberry.type(description="Added in 26.3.0. Entity edge")
class EntityEdge:
    node: EntityNode
    cursor: str


@strawberry.type(description="Added in 26.3.0. Entity connection")
class EntityConnection:
    edges: list[EntityEdge]
    page_info: strawberry.relay.PageInfo
    count: int
