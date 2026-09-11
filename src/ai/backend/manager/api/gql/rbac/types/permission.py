"""GraphQL types for RBAC permission management."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING, Annotated, Any, Self, cast, override
from uuid import UUID

import strawberry
from strawberry import Info
from strawberry.relay import Connection, Edge, NodeID

from ai.backend.common.data.entity.permission import PermissionID
from ai.backend.common.data.entity.role import RoleID
from ai.backend.common.dto.manager.v2.rbac.request import (
    BulkAddRolePermissionsInput as BulkAddRolePermissionsInputDTO,
)
from ai.backend.common.dto.manager.v2.rbac.request import (
    BulkRemoveRolePermissionsInput as BulkRemoveRolePermissionsInputDTO,
)
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
    PermissionNestedFilter as PermissionNestedFilterDTO,
)
from ai.backend.common.dto.manager.v2.rbac.request import (
    PermissionOrderBy as PermissionOrderByDTO,
)
from ai.backend.common.dto.manager.v2.rbac.request import (
    ReplaceRolePermissionsInput as ReplaceRolePermissionsInputDTO,
)
from ai.backend.common.dto.manager.v2.rbac.request import (
    UpdatePermissionInput as UpdatePermissionInputDTO,
)
from ai.backend.common.dto.manager.v2.rbac.response import (
    BulkAddRolePermissionFailureInfo as BulkAddRolePermissionFailureInfoDTO,
)
from ai.backend.common.dto.manager.v2.rbac.response import (
    BulkAddRolePermissionsPayload as BulkAddRolePermissionsPayloadDTO,
)
from ai.backend.common.dto.manager.v2.rbac.response import (
    BulkRemoveRolePermissionFailureInfo as BulkRemoveRolePermissionFailureInfoDTO,
)
from ai.backend.common.dto.manager.v2.rbac.response import (
    BulkRemoveRolePermissionsPayload as BulkRemoveRolePermissionsPayloadDTO,
)
from ai.backend.common.dto.manager.v2.rbac.response import (
    DeletePermissionPayload as DeletePermissionPayloadDTO,
)
from ai.backend.common.dto.manager.v2.rbac.response import (
    EntityActionInfo,
    EntityOperationCombinationInfo,
    OperationInfo,
    ScopeEntityCombinationInfo,
    ScopeEntityOperationCombinationInfo,
)
from ai.backend.common.dto.manager.v2.rbac.response import (
    PermissionNode as PermissionNodeDTO,
)
from ai.backend.common.dto.manager.v2.rbac.response import (
    ReplaceRolePermissionFailureInfo as ReplaceRolePermissionFailureInfoDTO,
)
from ai.backend.common.dto.manager.v2.rbac.response import (
    ReplaceRolePermissionsPayload as ReplaceRolePermissionsPayloadDTO,
)
from ai.backend.common.dto.manager.v2.rbac.types import (
    PermissionBitFilter as PermissionBitFilterDTO,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.base import DateTimeFilter, OrderDirection, StringFilter, UUIDFilter
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    PydanticInputMixin,
    gql_added_field,
    gql_connection_type,
    gql_enum,
    gql_field,
    gql_node_type,
    gql_pydantic_input,
    gql_pydantic_type,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin, PydanticOutputMixin
from ai.backend.manager.api.gql.rbac.types.scope import (
    PermissionBitGQL,
)
from ai.backend.manager.api.gql.types import GQLFilter, GQLOrderBy, StrawberryGQLContext

if TYPE_CHECKING:
    from ai.backend.manager.api.gql.rbac.types.role import RoleGQL

# ==================== Enums ====================


@gql_pydantic_input(
    BackendAIGQLMeta(
        description=(
            "Filter for a permission-bit column. Supports equals / in / not_equals / not_in."
        ),
        added_version=NEXT_RELEASE_VERSION,
    ),
    name="PermissionBitFilter",
)
class PermissionBitFilterGQL(PydanticInputMixin[PermissionBitFilterDTO]):
    equals: PermissionBitGQL | None = gql_field(
        description="Matches rows with this exact bit.", default=None
    )
    in_: list[PermissionBitGQL] | None = gql_field(
        description="Matches rows whose bit is in this list.",
        name="in",
        default=None,
    )
    not_equals: PermissionBitGQL | None = gql_field(
        description="Excludes rows with this exact bit.", default=None
    )
    not_in: list[PermissionBitGQL] | None = gql_field(
        description="Excludes rows whose bit is in this list.", default=None
    )


@gql_enum(BackendAIGQLMeta(added_version="26.3.0", description="Permission ordering field"))
class PermissionOrderField(StrEnum):
    ID = "id"
    ENTITY_TYPE = "entity_type"
    CREATED_AT = "created_at"


# ==================== Node Types ====================


@gql_node_type(
    BackendAIGQLMeta(added_version="26.3.0", description="RBAC scoped permission."),
    name="Permission",
)
class PermissionGQL(PydanticNodeMixin[PermissionNodeDTO]):
    id: NodeID[str]
    role_id: UUID
    entity_type: str
    created_at: datetime
    permission: PermissionBitGQL = gql_added_field(
        BackendAIGQLMeta(
            added_version=NEXT_RELEASE_VERSION,
            description="The permission bit the row holds.",
        )
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
        # DataLoader already returns PermissionGQL | None via from_pydantic conversion
        results = await info.context.data_loaders.permission_loader.load_many([
            PermissionID(UUID(nid)) for nid in node_ids
        ])
        return cast(list[Self | None], results)

    @gql_field(description="The role this permission belongs to.")  # type: ignore[misc]
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
        return await info.context.data_loaders.role_loader.load(RoleID(self.role_id))


# ==================== Filter Types ====================


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Nested filter for permissions within a role assignment. Filters assignments where the assigned role has permissions matching all specified conditions.",
        added_version="26.4.0",
    ),
    name="PermissionNestedFilter",
)
class PermissionNestedFilterGQL(PydanticInputMixin[PermissionNestedFilterDTO]):
    entity_type: StringFilter | None = None
    permission: PermissionBitFilterGQL | None = None

    AND: list[Self] | None = None
    OR: list[Self] | None = None
    NOT: list[Self] | None = None


@gql_pydantic_input(
    BackendAIGQLMeta(description="Filter for scoped permissions", added_version="26.3.0"),
    name="PermissionFilter",
)
class PermissionFilter(PydanticInputMixin[PermissionFilterDTO], GQLFilter):
    role_id: UUIDFilter | None = None
    entity_type: StringFilter | None = None
    created_at: DateTimeFilter | None = None
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
    role_id: UUID
    entity_type: str
    permission: PermissionBitGQL


@gql_pydantic_input(
    BackendAIGQLMeta(description="Input for updating a scoped permission", added_version="26.3.0"),
)
class UpdatePermissionInput(PydanticInputMixin[UpdatePermissionInputDTO]):
    id: UUID
    entity_type: str | None = None
    permission: PermissionBitGQL | None = None


@gql_pydantic_input(
    BackendAIGQLMeta(description="Input for deleting a scoped permission", added_version="26.3.0"),
)
class DeletePermissionInput(PydanticInputMixin[DeletePermissionInputDTO]):
    id: UUID


# -------- Bulk role-permission inputs --------


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Input for bulk-inserting scoped permissions across one or more roles",
        added_version="26.4.4",
    ),
    name="BulkAddRolePermissionsInput",
)
class BulkAddRolePermissionsInputGQL(PydanticInputMixin[BulkAddRolePermissionsInputDTO]):
    permissions: list[CreatePermissionInput]


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Input for bulk-deleting permission rows by primary key",
        added_version="26.4.4",
    ),
    name="BulkRemoveRolePermissionsInput",
)
class BulkRemoveRolePermissionsInputGQL(PydanticInputMixin[BulkRemoveRolePermissionsInputDTO]):
    permission_ids: list[UUID]


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Input for replacing one role's entire scoped-permission set",
        added_version="26.4.4",
    ),
    name="ReplaceRolePermissionsInput",
)
class ReplaceRolePermissionsInputGQL(PydanticInputMixin[ReplaceRolePermissionsInputDTO]):
    role_id: UUID
    permissions: list[CreatePermissionInput]


# ==================== Payload Types ====================


@gql_pydantic_type(
    BackendAIGQLMeta(added_version="26.3.0", description="Payload for delete permission mutation."),
    model=DeletePermissionPayloadDTO,
    name="DeletePermissionPayload",
)
class DeletePermissionPayload(PydanticOutputMixin[DeletePermissionPayloadDTO]):
    id: UUID = gql_field(description="ID of the deleted permission.")


# -------- Bulk role-permission payloads --------


@gql_pydantic_type(
    BackendAIGQLMeta(
        description="Failure detail for a single permission entry in bulk add",
        added_version="26.4.4",
    ),
    model=BulkAddRolePermissionFailureInfoDTO,
    name="BulkAddRolePermissionFailureInfo",
)
class BulkAddRolePermissionFailureInfoGQL(
    PydanticOutputMixin[BulkAddRolePermissionFailureInfoDTO],
):
    role_id: UUID = gql_field(description="Role ID of the failed entry.")
    entity_type: str = gql_field(description="Entity element type of the failed entry.")
    permission: PermissionBitGQL = gql_field(description="Operation bit of the failed entry.")
    message: str = gql_field(description="Error message describing the failure.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        description="Failure detail for a single permission ID in bulk remove",
        added_version="26.4.4",
    ),
    model=BulkRemoveRolePermissionFailureInfoDTO,
    name="BulkRemoveRolePermissionFailureInfo",
)
class BulkRemoveRolePermissionFailureInfoGQL(
    PydanticOutputMixin[BulkRemoveRolePermissionFailureInfoDTO],
):
    permission_id: UUID = gql_field(description="Permission row ID that failed to delete.")
    message: str = gql_field(description="Error message describing the failure.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        description="Failure detail for a single permission entry in replace",
        added_version="26.4.4",
    ),
    model=ReplaceRolePermissionFailureInfoDTO,
    name="ReplaceRolePermissionFailureInfo",
)
class ReplaceRolePermissionFailureInfoGQL(
    PydanticOutputMixin[ReplaceRolePermissionFailureInfoDTO],
):
    role_id: UUID = gql_field(description="Role ID of the failed entry.")
    entity_type: str = gql_field(description="Entity element type of the failed entry.")
    permission: PermissionBitGQL = gql_field(description="Operation bit of the failed entry.")
    message: str = gql_field(description="Error message describing the failure.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        description="Payload for bulk role-permission insertion",
        added_version="26.4.4",
    ),
    model=BulkAddRolePermissionsPayloadDTO,
    name="BulkAddRolePermissionsPayload",
)
class BulkAddRolePermissionsPayloadGQL(
    PydanticOutputMixin[BulkAddRolePermissionsPayloadDTO],
):
    items: list[PermissionGQL] = gql_field(description="Successfully inserted permission rows.")
    failed: list[BulkAddRolePermissionFailureInfoGQL] = gql_field(
        description="Permission entries that failed to insert."
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        description="Payload for bulk role-permission deletion",
        added_version="26.4.4",
    ),
    model=BulkRemoveRolePermissionsPayloadDTO,
    name="BulkRemoveRolePermissionsPayload",
)
class BulkRemoveRolePermissionsPayloadGQL(
    PydanticOutputMixin[BulkRemoveRolePermissionsPayloadDTO],
):
    items: list[PermissionGQL] = gql_field(description="Successfully deleted permission rows.")
    failed: list[BulkRemoveRolePermissionFailureInfoGQL] = gql_field(
        description="Permission IDs that failed to delete."
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        description="Payload for replacing a role's entire scoped-permission set",
        added_version="26.4.4",
    ),
    model=ReplaceRolePermissionsPayloadDTO,
    name="ReplaceRolePermissionsPayload",
)
class ReplaceRolePermissionsPayloadGQL(
    PydanticOutputMixin[ReplaceRolePermissionsPayloadDTO],
):
    items: list[PermissionGQL] = gql_field(description="Permission rows that make up the new set.")
    failed: list[ReplaceRolePermissionFailureInfoGQL] = gql_field(
        description="Permission entries that failed to insert.",
        deprecation_reason=(
            "Always empty. The write states the whole set or raises; a later API reports"
            " what it refused."
        ),
    )


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
    scope_type: str
    valid_entity_types: list[str]


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Information about a single RBAC operation.",
    ),
    model=OperationInfo,
    name="OperationInfo",
)
class OperationInfoGQL(PydanticOutputMixin[OperationInfo]):
    operation: str
    description: str
    required_permission: PermissionBitGQL


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Valid entity-operation combination for RBAC actions.",
    ),
    model=EntityOperationCombinationInfo,
    name="EntityOperationCombination",
)
class EntityOperationCombinationGQL(PydanticOutputMixin[EntityOperationCombinationInfo]):
    entity_type: str
    operations: list[OperationInfoGQL]


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Entity with its allowed actions within a scope.",
    ),
    model=EntityActionInfo,
    name="EntityActionInfo",
)
class EntityActionInfoGQL(PydanticOutputMixin[EntityActionInfo]):
    entity_type: str
    actions: list[OperationInfoGQL]


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Scope-entity-operation combination for RBAC permission matrix.",
    ),
    model=ScopeEntityOperationCombinationInfo,
    name="ScopeEntityOperationCombination",
)
class ScopeEntityOperationCombinationGQL(
    PydanticOutputMixin[ScopeEntityOperationCombinationInfo],
):
    scope_type: str
    entities: list[EntityActionInfoGQL]


PermissionEdge = Edge[PermissionGQL]


@gql_connection_type(BackendAIGQLMeta(added_version="26.3.0", description="Permission connection."))
class PermissionConnection(Connection[PermissionGQL]):
    count: int

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count
