"""GraphQL types for RBAC entity search."""

from __future__ import annotations

import uuid
from collections.abc import Iterable
from datetime import datetime
from enum import StrEnum
from typing import Any, Self, cast, override

from strawberry import Info
from strawberry.relay import Connection, Edge, NodeID

from ai.backend.common.data.entity.types import EntityType, RuntimeEntityID
from ai.backend.common.dto.manager.v2.rbac.request import (
    EntityFilter as EntityFilterDTO,
)
from ai.backend.common.dto.manager.v2.rbac.request import (
    EntityOrderBy as EntityOrderByDTO,
)
from ai.backend.common.dto.manager.v2.rbac.response import (
    AssociationScopesEntitiesNode,
)
from ai.backend.manager.api.gql.base import OrderDirection, StringFilter
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    PydanticInputMixin,
    gql_added_field,
    gql_connection_type,
    gql_enum,
    gql_field,
    gql_node_type,
    gql_pydantic_input,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin
from ai.backend.manager.api.gql.rbac.types.entity_node import EntityNode
from ai.backend.manager.api.gql.rbac.types.scope import EntityTypeFilterGQL
from ai.backend.manager.api.gql.types import GQLFilter, GQLOrderBy, StrawberryGQLContext

# ==================== Enums ====================


@gql_enum(BackendAIGQLMeta(added_version="26.3.0", description="Entity ordering field"))
class EntityOrderField(StrEnum):
    ENTITY_TYPE = "entity_type"
    REGISTERED_AT = "registered_at"


# ==================== Node Types ====================


@gql_node_type(
    BackendAIGQLMeta(
        added_version="26.3.0",
        description="Entity reference from the association_scopes_entities table.",
    ),
    name="EntityRef",
)
class EntityRefGQL(PydanticNodeMixin[AssociationScopesEntitiesNode]):
    id: NodeID[str]
    scope_type: str
    scope_id: str
    entity_type: str
    entity_id: str
    registered_at: datetime

    @gql_field(description="The resolved entity object.")  # type: ignore[misc]
    async def entity(
        self,
        *,
        info: Info[StrawberryGQLContext],
    ) -> EntityNode | None:
        return await info.context.data_loaders.entity_node_loader.load(
            RuntimeEntityID(EntityType(str(self.entity_type)), uuid.UUID(self.entity_id))
        )

    @gql_added_field(
        BackendAIGQLMeta(
            added_version="26.4.3",
            description="The resolved scope object in which the entity is registered.",
        )
    )  # type: ignore[misc]
    async def scope(
        self,
        *,
        info: Info[StrawberryGQLContext],
    ) -> EntityNode | None:
        return await info.context.data_loaders.entity_node_loader.load(
            RuntimeEntityID(EntityType(str(self.scope_type)), uuid.UUID(self.scope_id))
        )

    @classmethod
    @override
    async def resolve_nodes(  # type: ignore[override]
        cls,
        *,
        info: Info[StrawberryGQLContext],
        node_ids: Iterable[str],
        required: bool = False,
    ) -> Iterable[Self | None]:
        # DataLoader already returns EntityRefGQL | None via from_pydantic conversion
        results = await info.context.data_loaders.element_association_loader.load_many([
            uuid.UUID(nid) for nid in node_ids
        ])
        return cast(list[Self | None], results)


# ==================== Filter Types ====================


@gql_pydantic_input(
    BackendAIGQLMeta(description="Filter for entity associations", added_version="26.3.0"),
    name="EntityFilter",
)
class EntityFilter(PydanticInputMixin[EntityFilterDTO], GQLFilter):
    entity_type: EntityTypeFilterGQL | None = None
    entity_id: StringFilter | None = None
    scope_type: EntityTypeFilterGQL | None = gql_added_field(
        BackendAIGQLMeta(
            added_version="26.8.0",
            description="Filter by the type of scope the entity is registered in.",
        ),
        default=None,
    )
    scope_id: StringFilter | None = gql_added_field(
        BackendAIGQLMeta(
            added_version="26.8.0",
            description="Filter by the id of scope the entity is registered in.",
        ),
        default=None,
    )
    AND: list[Self] | None = None
    OR: list[Self] | None = None
    NOT: list[Self] | None = None


# ==================== OrderBy Types ====================


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Order by specification for entity associations", added_version="26.3.0"
    ),
    name="EntityOrderBy",
)
class EntityOrderBy(PydanticInputMixin[EntityOrderByDTO], GQLOrderBy):
    field: EntityOrderField
    direction: OrderDirection = OrderDirection.DESC


# ==================== Connection Types ====================

EntityEdge = Edge[EntityRefGQL]


@gql_connection_type(BackendAIGQLMeta(added_version="26.3.0", description="Entity connection."))
class EntityConnection(Connection[EntityRefGQL]):
    count: int

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count
