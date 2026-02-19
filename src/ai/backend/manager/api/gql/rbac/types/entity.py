"""GraphQL types for RBAC entity search."""

from __future__ import annotations

import uuid
from collections.abc import Iterable
from datetime import datetime
from enum import StrEnum
from typing import Self, override

import strawberry
from strawberry import ID, Info
from strawberry.relay import Node, NodeID

from ai.backend.manager.api.gql.base import OrderDirection, StringFilter
from ai.backend.manager.api.gql.rbac.types.entity_node import EntityNode
from ai.backend.manager.api.gql.rbac.types.permission import RBACElementTypeGQL
from ai.backend.manager.api.gql.types import GQLFilter, GQLOrderBy, StrawberryGQLContext
from ai.backend.manager.data.permission.association_scopes_entities import (
    AssociationScopesEntitiesData,
)
from ai.backend.manager.data.permission.types import EntityType
from ai.backend.manager.repositories.base import QueryCondition, QueryOrder
from ai.backend.manager.repositories.permission_controller.options import (
    EntityScopeConditions,
    EntityScopeOrders,
)

# ==================== Enums ====================


@strawberry.enum(description="Added in 26.3.0. Entity ordering field")
class EntityOrderField(StrEnum):
    ENTITY_TYPE = "entity_type"
    REGISTERED_AT = "registered_at"


# ==================== Node Types ====================


@strawberry.type(
    name="EntityRef",
    description="Added in 26.3.0. Entity reference from the association_scopes_entities table",
)
class EntityRefGQL(Node):
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
        from ai.backend.common.types import ImageID
        from ai.backend.manager.api.gql.artifact.types import ArtifactRevision
        from ai.backend.manager.api.gql.deployment.types.deployment import ModelDeployment
        from ai.backend.manager.api.gql.domain_v2.types.node import DomainV2GQL
        from ai.backend.manager.api.gql.image.types import ImageV2GQL
        from ai.backend.manager.api.gql.notification.types import (
            NotificationChannel,
            NotificationRule,
        )
        from ai.backend.manager.api.gql.project_v2.types.node import ProjectV2GQL
        from ai.backend.manager.api.gql.rbac.types.role import RoleGQL
        from ai.backend.manager.api.gql.resource_group.types import ResourceGroupGQL
        from ai.backend.manager.api.gql.user.types.node import UserV2GQL

        entity_type = self.entity_type.to_internal()
        data_loaders = info.context.data_loaders
        match entity_type:
            case EntityType.USER:
                user_data = await data_loaders.user_loader.load(uuid.UUID(self.entity_id))
                if user_data is None:
                    return None
                return UserV2GQL.from_data(user_data)
            case EntityType.PROJECT:
                project_data = await data_loaders.project_loader.load(uuid.UUID(self.entity_id))
                if project_data is None:
                    return None
                return ProjectV2GQL.from_data(project_data)
            case EntityType.DOMAIN:
                domain_data = await data_loaders.domain_loader.load(self.entity_id)
                if domain_data is None:
                    return None
                return DomainV2GQL.from_data(domain_data)
            case EntityType.ROLE:
                role_data = await data_loaders.role_loader.load(uuid.UUID(self.entity_id))
                if role_data is None:
                    return None
                return RoleGQL.from_dataclass(role_data)
            case EntityType.IMAGE:
                image_data = await data_loaders.image_loader.load(
                    ImageID(uuid.UUID(self.entity_id))
                )
                if image_data is None:
                    return None
                return ImageV2GQL.from_data(image_data)
            case EntityType.MODEL_DEPLOYMENT:
                deploy_data = await data_loaders.deployment_loader.load(uuid.UUID(self.entity_id))
                if deploy_data is None:
                    return None
                return ModelDeployment.from_dataclass(deploy_data)
            case EntityType.RESOURCE_GROUP:
                rg_data = await data_loaders.resource_group_loader.load(self.entity_id)
                if rg_data is None:
                    return None
                return ResourceGroupGQL.from_dataclass(rg_data)
            case EntityType.NOTIFICATION_CHANNEL:
                channel_data = await data_loaders.notification_channel_loader.load(
                    uuid.UUID(self.entity_id)
                )
                if channel_data is None:
                    return None
                return NotificationChannel.from_dataclass(channel_data)
            case EntityType.NOTIFICATION_RULE:
                rule_data = await data_loaders.notification_rule_loader.load(
                    uuid.UUID(self.entity_id)
                )
                if rule_data is None:
                    return None
                return NotificationRule.from_dataclass(rule_data)
            case EntityType.ARTIFACT_REVISION:
                rev_data = await data_loaders.artifact_revision_loader.load(
                    uuid.UUID(self.entity_id)
                )
                if rev_data is None:
                    return None
                return ArtifactRevision.from_dataclass(rev_data)
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
        results = await info.context.data_loaders.element_association_loader.load_many([
            uuid.UUID(nid) for nid in node_ids
        ])
        return [cls.from_dataclass(data) if data is not None else None for data in results]

    @classmethod
    def from_dataclass(cls, data: AssociationScopesEntitiesData) -> Self:
        return cls(
            id=ID(str(data.id)),
            scope_type=RBACElementTypeGQL.from_element(data.scope_id.scope_type.to_element()),
            scope_id=data.scope_id.scope_id,
            entity_type=RBACElementTypeGQL.from_element(data.object_id.entity_type.to_element()),
            entity_id=data.object_id.entity_id,
            registered_at=data.registered_at,
        )


# ==================== Filter Types ====================


@strawberry.input(description="Added in 26.3.0. Filter for entity associations")
class EntityFilter(GQLFilter):
    entity_type: RBACElementTypeGQL | None = None
    entity_id: StringFilter | None = None

    @override
    def build_conditions(self) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []

        if self.entity_type is not None:
            conditions.append(
                EntityScopeConditions.by_entity_type(self.entity_type.to_element().to_entity_type())
            )

        if self.entity_id is not None:
            condition = self.entity_id.build_query_condition(
                contains_factory=EntityScopeConditions.by_entity_id_contains,
                equals_factory=EntityScopeConditions.by_entity_id_equals,
                starts_with_factory=EntityScopeConditions.by_entity_id_starts_with,
                ends_with_factory=EntityScopeConditions.by_entity_id_ends_with,
            )
            if condition:
                conditions.append(condition)

        return conditions


# ==================== OrderBy Types ====================


@strawberry.input(description="Added in 26.3.0. Order by specification for entity associations")
class EntityOrderBy(GQLOrderBy):
    field: EntityOrderField
    direction: OrderDirection = OrderDirection.DESC

    @override
    def to_query_order(self) -> QueryOrder:
        ascending = self.direction == OrderDirection.ASC
        match self.field:
            case EntityOrderField.ENTITY_TYPE:
                return EntityScopeOrders.entity_type(ascending)
            case EntityOrderField.REGISTERED_AT:
                return EntityScopeOrders.registered_at(ascending)


# ==================== Connection Types ====================


@strawberry.type(description="Added in 26.3.0. Entity edge")
class EntityEdge:
    node: EntityRefGQL
    cursor: str


@strawberry.type(description="Added in 26.3.0. Entity connection")
class EntityConnection:
    edges: list[EntityEdge]
    page_info: strawberry.relay.PageInfo
    count: int
