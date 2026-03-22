"""GraphQL types for RBAC entity search."""

from __future__ import annotations

import uuid
from collections.abc import Iterable
from datetime import datetime
from enum import StrEnum
from typing import Any, Self, cast

import strawberry
from strawberry import Info
from strawberry.relay import Connection, Edge, NodeID

from ai.backend.common.data.permission.types import RBACElementType
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
    gql_connection_type,
    gql_node_type,
    gql_pydantic_input,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin
from ai.backend.manager.api.gql.rbac.types.entity_node import EntityNode
from ai.backend.manager.api.gql.rbac.types.permission import RBACElementTypeGQL
from ai.backend.manager.api.gql.types import GQLFilter, GQLOrderBy, StrawberryGQLContext

# ==================== Enums ====================


@strawberry.enum(description="Added in 26.3.0. Entity ordering field")
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
    scope_type: RBACElementTypeGQL
    scope_id: str
    entity_type: RBACElementTypeGQL
    entity_id: str
    registered_at: datetime

    @strawberry.field(  # type: ignore[misc]
        description="The resolved entity object."
    )
    async def entity(
        self,
        *,
        info: Info[StrawberryGQLContext],
    ) -> EntityNode | None:
        from ai.backend.common.types import ImageID, SessionId

        element_type = RBACElementType(self.entity_type.value)
        data_loaders = info.context.data_loaders
        match element_type:
            case RBACElementType.USER:
                # DataLoader already returns UserV2GQL | None via from_pydantic conversion
                return await data_loaders.user_loader.load(uuid.UUID(self.entity_id))
            case RBACElementType.PROJECT:
                # DataLoader already returns ProjectV2GQL | None via from_pydantic conversion
                return await data_loaders.project_loader.load(uuid.UUID(self.entity_id))
            case RBACElementType.DOMAIN:
                return await data_loaders.domain_loader.load(self.entity_id)
            case RBACElementType.ROLE:
                # DataLoader already returns RoleGQL | None via from_pydantic conversion
                return await data_loaders.role_loader.load(uuid.UUID(self.entity_id))
            case RBACElementType.IMAGE:
                # DataLoader already returns ImageV2GQL | None via from_pydantic conversion
                return await data_loaders.image_loader.load(ImageID(uuid.UUID(self.entity_id)))
            case RBACElementType.MODEL_DEPLOYMENT:
                # DataLoader already returns ModelDeployment | None via from_pydantic conversion
                return await data_loaders.deployment_loader.load(uuid.UUID(self.entity_id))
            case RBACElementType.RESOURCE_GROUP:
                return await data_loaders.resource_group_loader.load(self.entity_id)
            case RBACElementType.NOTIFICATION_CHANNEL:
                return await data_loaders.notification_channel_loader.load(
                    uuid.UUID(self.entity_id)
                )
            case RBACElementType.NOTIFICATION_RULE:
                return await data_loaders.notification_rule_loader.load(uuid.UUID(self.entity_id))
            case RBACElementType.ARTIFACT_REVISION:
                # DataLoader already returns ArtifactRevision | None via from_pydantic
                return await data_loaders.artifact_revision_loader.load(uuid.UUID(self.entity_id))
            case RBACElementType.CONTAINER_REGISTRY:
                # DataLoader already returns ContainerRegistryGQL | None via from_pydantic
                return await data_loaders.container_registry_loader.load(uuid.UUID(self.entity_id))
            case RBACElementType.SESSION:
                # DataLoader already returns SessionV2GQL | None via from_pydantic conversion
                return await data_loaders.session_loader.load(SessionId(uuid.UUID(self.entity_id)))
            case _:
                return None

    @classmethod
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
    entity_type: RBACElementTypeGQL | None = None
    entity_id: StringFilter | None = None
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
