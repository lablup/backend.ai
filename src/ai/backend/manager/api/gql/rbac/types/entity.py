"""Compatibility GQL types for the deprecated `Role.scopes` connection.

A role belongs to one scope, held on the role itself. These types keep the shape
`Role.scopes` published while a role was registered in scopes through an association
table.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterable
from datetime import datetime
from enum import StrEnum
from typing import Any, Self, override

from strawberry import Info
from strawberry.relay import Connection, Edge, NodeID

from ai.backend.common.data.entity.role import RoleEntityType, RoleID
from ai.backend.common.data.entity.types import EntityType, RuntimeEntityID
from ai.backend.common.dto.manager.v2.rbac.request import (
    EntityFilter as EntityFilterDTO,
)
from ai.backend.common.dto.manager.v2.rbac.request import (
    EntityOrderBy as EntityOrderByDTO,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
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
from ai.backend.manager.api.gql.rbac.types.entity_node import EntityNodeGQL
from ai.backend.manager.api.gql.rbac.types.role import RoleGQL
from ai.backend.manager.api.gql.types import GQLFilter, GQLOrderBy, StrawberryGQLContext

# ==================== Enums ====================


@gql_enum(
    BackendAIGQLMeta(
        added_version="26.3.0",
        description="Entity ordering field",
        deprecated_version=NEXT_RELEASE_VERSION,
        deprecation_hint="`Role.scope`",
    )
)
class EntityOrderField(StrEnum):
    ENTITY_TYPE = "entity_type"
    REGISTERED_AT = "registered_at"


# ==================== Node Types ====================


@gql_node_type(
    BackendAIGQLMeta(
        added_version="26.3.0",
        description="A role and the scope it belongs to.",
        deprecated_version=NEXT_RELEASE_VERSION,
        deprecation_hint="`Role.scope`",
    ),
    name="EntityRef",
)
class EntityRefGQL(PydanticNodeMixin[Any]):
    id: NodeID[str]
    scope_type: str
    scope_id: str
    entity_type: str
    entity_id: str
    registered_at: datetime

    @classmethod
    def from_role(cls, role: RoleGQL) -> Self:
        return cls(
            id=str(role.id),
            scope_type=role.scope_type,
            scope_id=str(role.scope_id),
            entity_type=RoleEntityType.name(),
            entity_id=str(role.id),
            registered_at=role.created_at,
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
        roles = await info.context.data_loaders.role_loader.load_many([
            RoleID(uuid.UUID(nid)) for nid in node_ids
        ])
        return [None if role is None else cls.from_role(role) for role in roles]

    @gql_field(description="The resolved entity object.")  # type: ignore[misc]
    async def entity(
        self,
        *,
        info: Info[StrawberryGQLContext],
    ) -> EntityNodeGQL | None:
        return await info.context.data_loaders.entity_node_loader.load(
            RuntimeEntityID(EntityType.from_name(self.entity_type), uuid.UUID(self.entity_id))
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
    ) -> EntityNodeGQL | None:
        return await info.context.data_loaders.entity_node_loader.load(
            RuntimeEntityID(EntityType.from_name(self.scope_type), uuid.UUID(self.scope_id))
        )


# ==================== Filter Types ====================


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Filter for entity associations",
        added_version="26.3.0",
        deprecated_version=NEXT_RELEASE_VERSION,
        deprecation_hint="`Role.scope`",
    ),
    name="EntityFilter",
)
class EntityFilterGQL(PydanticInputMixin[EntityFilterDTO], GQLFilter):
    entity_type: StringFilter | None = None
    entity_id: StringFilter | None = None
    scope_type: StringFilter | None = gql_added_field(
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
        description="Order by specification for entity associations",
        added_version="26.3.0",
        deprecated_version=NEXT_RELEASE_VERSION,
        deprecation_hint="`Role.scope`",
    ),
    name="EntityOrderBy",
)
class EntityOrderByGQL(PydanticInputMixin[EntityOrderByDTO], GQLOrderBy):
    field: EntityOrderField
    direction: OrderDirection = OrderDirection.DESC


# ==================== Connection Types ====================

EntityEdge = Edge[EntityRefGQL]


@gql_connection_type(
    BackendAIGQLMeta(
        added_version="26.3.0",
        description="Entity connection.",
        deprecated_version=NEXT_RELEASE_VERSION,
        deprecation_hint="`Role.scope`",
    )
)
class EntityConnection(Connection[EntityRefGQL]):
    count: int

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count
