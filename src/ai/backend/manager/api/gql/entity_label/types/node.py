"""Label GQL Node, Edge, and Connection types."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from strawberry.relay import Connection, Edge, NodeID

from ai.backend.common.dto.manager.v2.entity_label.response import EntityLabelNode
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_connection_type,
    gql_field,
    gql_node_type,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin

__all__ = (
    "EntityLabelConnection",
    "EntityLabelEdge",
    "EntityLabelGQL",
)


@gql_node_type(
    BackendAIGQLMeta(
        description="One `key=value` label and the entity carrying it.",
        added_version=NEXT_RELEASE_VERSION,
    ),
    name="EntityLabel",
)
class EntityLabelGQL(PydanticNodeMixin[EntityLabelNode]):
    id: NodeID[str] = gql_field(description="Label UUID (primary key).")
    entity_type: str = gql_field(description="Type of the labeled entity.")
    entity_id: UUID = gql_field(description="ID of the labeled entity.")
    key: str = gql_field(description="Label key.")
    value: str = gql_field(description="Label value.")
    created_at: datetime = gql_field(description="When the label was first put on the entity.")
    updated_at: datetime = gql_field(description="When the label's value was last replaced.")


EntityLabelEdge = Edge[EntityLabelGQL]


@gql_connection_type(
    BackendAIGQLMeta(
        description="Paginated connection for label records.",
        added_version=NEXT_RELEASE_VERSION,
    ),
)
class EntityLabelConnection(Connection[EntityLabelGQL]):
    count: int = gql_field(description="Total number of label records matching the query criteria.")

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count
