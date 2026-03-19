"""GraphQL types for RBAC permission management."""

from __future__ import annotations

import uuid
from collections.abc import Iterable
from enum import StrEnum
from typing import TYPE_CHECKING, Annotated, Any, Self, cast

import strawberry
from strawberry import ID, Info
from strawberry.relay import Connection, Edge, NodeID

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.common.dto.manager.v2.rbac.request import (
    CreatePermissionInput as CreatePermissionInputDTO,
)
from ai.backend.common.dto.manager.v2.rbac.request import (
    DeletePermissionInput as DeletePermissionInputDTO,
)
from ai.backend.common.dto.manager.v2.rbac.request import (
    PermissionFilter as PermissionFilterDTO,
)
from ai.backend.common.dto.manager.v2.rbac.request import (
    PermissionOrderBy as PermissionOrderByDTO,
)
from ai.backend.common.dto.manager.v2.rbac.request import (
    UpdatePermissionInput as UpdatePermissionInputDTO,
)
from ai.backend.common.dto.manager.v2.rbac.response import (
    DeletePermissionPayload as DeletePermissionPayloadDTO,
)
from ai.backend.common.dto.manager.v2.rbac.response import (
    PermissionNode as PermissionNodeDTO,
)
from ai.backend.common.dto.manager.v2.rbac.response import (
    ScopeEntityCombinationInfo,
)
from ai.backend.common.dto.manager.v2.rbac.types import (
    OperationTypeDTO,
    RBACElementTypeDTO,
)
from ai.backend.common.types import SessionId
from ai.backend.manager.api.gql.base import OrderDirection
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    PydanticInputMixin,
    gql_connection_type,
    gql_node_type,
    gql_pydantic_input,
    gql_pydantic_type,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin, PydanticOutputMixin
from ai.backend.manager.api.gql.rbac.types.entity_node import EntityNode
from ai.backend.manager.api.gql.types import GQLFilter, GQLOrderBy, StrawberryGQLContext

if TYPE_CHECKING:
    from ai.backend.manager.api.gql.rbac.types.role import RoleGQL

# ==================== Enums ====================


RBACElementTypeGQL: type[RBACElementTypeDTO] = strawberry.enum(
    RBACElementTypeDTO,
    name="RBACElementType",
    description="Added in 26.3.0. Unified RBAC element type for scope-entity relationships",
)

OperationTypeGQL: type[OperationTypeDTO] = strawberry.enum(
    OperationTypeDTO,
    name="OperationType",
    description="Added in 26.3.0. RBAC operation type",
)


@strawberry.enum(description="Added in 26.3.0. Permission ordering field")
class PermissionOrderField(StrEnum):
    ID = "id"
    ENTITY_TYPE = "entity_type"


# ==================== Node Types ====================


@gql_node_type(
    BackendAIGQLMeta(added_version="26.3.0", description="RBAC scoped permission."),
    name="Permission",
)
class PermissionGQL(PydanticNodeMixin[PermissionNodeDTO]):
    id: NodeID[str]
    role_id: uuid.UUID
    scope_type: RBACElementTypeGQL
    scope_id: str
    entity_type: RBACElementTypeGQL
    operation: OperationTypeGQL

    @classmethod
    async def resolve_nodes(  # type: ignore[override]
        cls,
        *,
        info: Info[StrawberryGQLContext],
        node_ids: Iterable[str],
        required: bool = False,
    ) -> Iterable[Self | None]:
        # DataLoader already returns PermissionGQL | None via from_pydantic conversion
        results = await info.context.data_loaders.permission_loader.load_many([
            uuid.UUID(nid) for nid in node_ids
        ])
        return cast(list[Self | None], results)

    @strawberry.field(description="The role this permission belongs to.")  # type: ignore[misc]
    async def role(
        self, info: Info[StrawberryGQLContext]
    ) -> (
        Annotated[
            RoleGQL,
            strawberry.lazy("ai.backend.manager.api.gql.rbac.types.role"),
        ]
        | None
    ):
        # DataLoader already returns RoleGQL | None via from_pydantic conversion
        return await info.context.data_loaders.role_loader.load(self.role_id)

    @strawberry.field(  # type: ignore[misc]
        description="The scope this permission applies to."
    )
    async def scope(
        self,
        *,
        info: Info[StrawberryGQLContext],
    ) -> EntityNode | None:
        element_type = RBACElementType(self.scope_type.value)
        data_loaders = info.context.data_loaders
        match element_type:
            case RBACElementType.USER:
                # DataLoader already returns UserV2GQL | None via from_pydantic conversion
                return await data_loaders.user_loader.load(uuid.UUID(self.scope_id))
            case RBACElementType.PROJECT:
                # DataLoader already returns ProjectV2GQL | None via from_pydantic conversion
                return await data_loaders.project_loader.load(uuid.UUID(self.scope_id))
            case RBACElementType.DOMAIN:
                return await data_loaders.domain_loader.load(self.scope_id)
            case RBACElementType.ROLE:
                # DataLoader already returns RoleGQL | None via from_pydantic conversion
                return await data_loaders.role_loader.load(uuid.UUID(self.scope_id))
            case RBACElementType.RESOURCE_GROUP:
                return await data_loaders.resource_group_loader.load(self.scope_id)
            case RBACElementType.MODEL_DEPLOYMENT:
                # DataLoader already returns ModelDeployment | None via from_pydantic conversion
                return await data_loaders.deployment_loader.load(uuid.UUID(self.scope_id))
            case RBACElementType.ARTIFACT_REVISION:
                # DataLoader already returns ArtifactRevision | None via from_pydantic
                return await data_loaders.artifact_revision_loader.load(uuid.UUID(self.scope_id))
            case RBACElementType.CONTAINER_REGISTRY:
                # DataLoader already returns ContainerRegistryGQL | None via from_pydantic
                return await data_loaders.container_registry_loader.load(uuid.UUID(self.scope_id))
            case RBACElementType.SESSION:
                # DataLoader already returns SessionV2GQL | None via from_pydantic conversion
                return await data_loaders.session_loader.load(SessionId(uuid.UUID(self.scope_id)))
            case (
                RBACElementType.VFOLDER
                | RBACElementType.KEYPAIR
                | RBACElementType.NOTIFICATION_CHANNEL
                | RBACElementType.NETWORK
                | RBACElementType.STORAGE_HOST
                | RBACElementType.IMAGE
                | RBACElementType.ARTIFACT
                | RBACElementType.ARTIFACT_REGISTRY
                | RBACElementType.SESSION_TEMPLATE
                | RBACElementType.APP_CONFIG
                | RBACElementType.RESOURCE_PRESET
                | RBACElementType.USER_RESOURCE_POLICY
                | RBACElementType.KEYPAIR_RESOURCE_POLICY
                | RBACElementType.PROJECT_RESOURCE_POLICY
                | RBACElementType.AUDIT_LOG
                | RBACElementType.EVENT_LOG
                | RBACElementType.NOTIFICATION_RULE
                | RBACElementType.AGENT
                | RBACElementType.KERNEL
                | RBACElementType.ROUTING
                | RBACElementType.DEPLOYMENT_TOKEN
                | RBACElementType.DEPLOYMENT_POLICY
                | RBACElementType.DEPLOYMENT_REVISION
                | RBACElementType.IMAGE_ALIAS
                | RBACElementType.PROJECT_ADMIN_PAGE
                | RBACElementType.DOMAIN_ADMIN_PAGE
            ):
                return None


# ==================== Filter Types ====================


@gql_pydantic_input(
    BackendAIGQLMeta(description="Filter for scoped permissions", added_version="26.3.0"),
    name="PermissionFilter",
)
class PermissionFilter(PydanticInputMixin[PermissionFilterDTO], GQLFilter):
    role_id: uuid.UUID | None = None
    scope_type: RBACElementTypeGQL | None = None
    entity_type: RBACElementTypeGQL | None = None
    AND: list[Self] | None = None
    OR: list[Self] | None = None
    NOT: list[Self] | None = None


# ==================== OrderBy Types ====================


@gql_pydantic_input(
    BackendAIGQLMeta(description="Order by specification for permissions", added_version="26.3.0"),
    name="PermissionOrderBy",
)
class PermissionOrderBy(PydanticInputMixin[PermissionOrderByDTO], GQLOrderBy):
    field: PermissionOrderField
    direction: OrderDirection = OrderDirection.DESC


# ==================== Input Types ====================


@gql_pydantic_input(
    BackendAIGQLMeta(description="Input for creating a scoped permission", added_version="26.3.0"),
)
class CreatePermissionInput(PydanticInputMixin[CreatePermissionInputDTO]):
    role_id: uuid.UUID
    scope_type: RBACElementTypeGQL
    scope_id: str
    entity_type: RBACElementTypeGQL
    operation: OperationTypeGQL


@gql_pydantic_input(
    BackendAIGQLMeta(description="Input for updating a scoped permission", added_version="26.3.0"),
)
class UpdatePermissionInput(PydanticInputMixin[UpdatePermissionInputDTO]):
    id: uuid.UUID
    scope_type: RBACElementTypeGQL | None = None
    scope_id: str | None = None
    entity_type: RBACElementTypeGQL | None = None
    operation: OperationTypeGQL | None = None


@gql_pydantic_input(
    BackendAIGQLMeta(description="Input for deleting a scoped permission", added_version="26.3.0"),
)
class DeletePermissionInput(PydanticInputMixin[DeletePermissionInputDTO]):
    id: uuid.UUID


# ==================== Payload Types ====================


@gql_pydantic_type(
    BackendAIGQLMeta(added_version="26.3.0", description="Payload for delete permission mutation."),
    model=DeletePermissionPayloadDTO,
    fields=["id"],
    name="DeletePermissionPayload",
)
class DeletePermissionPayload(PydanticOutputMixin[DeletePermissionPayloadDTO]):
    id: ID = strawberry.field(description="ID of the deleted permission.")


# ==================== Connection Types ====================


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.3.0",
        description="Valid scope-entity type combination for RBAC permissions.",
    ),
    model=ScopeEntityCombinationInfo,
    name="ScopeEntityCombination",
)
class ScopeEntityCombinationGQL(PydanticOutputMixin[ScopeEntityCombinationInfo]):
    scope_type: RBACElementTypeGQL
    valid_entity_types: list[RBACElementTypeGQL]


PermissionEdge = Edge[PermissionGQL]


@gql_connection_type(BackendAIGQLMeta(added_version="26.3.0", description="Permission connection."))
class PermissionConnection(Connection[PermissionGQL]):
    count: int

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count
