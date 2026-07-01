"""Role permission preset GQL types (node, filter, order, payloads).

These types describe the permission entries carried by a role preset. They back
the ``permission_presets`` field resolver on ``RolePresetGQL`` and the bulk add/remove
permission mutations.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any, Self
from uuid import UUID

from strawberry.relay import Connection, Edge, NodeID

from ai.backend.common.dto.manager.v2.role_permission_preset.request import (
    RolePermissionPresetFilter as RolePermissionPresetFilterDTO,
)
from ai.backend.common.dto.manager.v2.role_permission_preset.request import (
    RolePermissionPresetOrder as RolePermissionPresetOrderDTO,
)
from ai.backend.common.dto.manager.v2.role_permission_preset.response import (
    BulkAddRolePermissionPresetFailureInfo as BulkAddRolePermissionPresetFailureInfoDTO,
)
from ai.backend.common.dto.manager.v2.role_permission_preset.response import (
    BulkAddRolePermissionPresetsPayload as BulkAddRolePermissionPresetsPayloadDTO,
)
from ai.backend.common.dto.manager.v2.role_permission_preset.response import (
    BulkRemoveRolePermissionPresetsPayload as BulkRemoveRolePermissionPresetsPayloadDTO,
)
from ai.backend.common.dto.manager.v2.role_permission_preset.response import (
    BulkRolePermissionPresetFailureInfo as BulkRolePermissionPresetFailureInfoDTO,
)
from ai.backend.common.dto.manager.v2.role_permission_preset.response import (
    RolePermissionPresetNode,
)
from ai.backend.manager.api.gql.base import (
    DateTimeFilter,
    OrderDirection,
    UUIDFilter,
)
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_connection_type,
    gql_enum,
    gql_field,
    gql_node_type,
    gql_pydantic_input,
    gql_pydantic_type,
)
from ai.backend.manager.api.gql.pydantic_compat import (
    PydanticInputMixin,
    PydanticNodeMixin,
    PydanticOutputMixin,
)
from ai.backend.manager.api.gql.rbac.types import (
    OperationTypeFilterGQL,
    OperationTypeGQL,
    RBACElementTypeFilterGQL,
    RBACElementTypeGQL,
)

# --- Node / Connection types ---


@gql_node_type(
    BackendAIGQLMeta(
        added_version="26.4.4",
        description="A stored permission entry under a role preset.",
    ),
    name="RolePermissionPreset",
)
class RolePermissionPresetGQL(PydanticNodeMixin[RolePermissionPresetNode]):
    id: NodeID[str] = gql_field(description="Permission entry UUID.")
    role_preset_id: UUID = gql_field(description="UUID of the parent role preset.")
    entity_type: RBACElementTypeGQL = gql_field(
        description="Entity type the permission applies to."
    )
    operation: OperationTypeGQL = gql_field(description="Operation granted by the permission.")
    created_at: datetime = gql_field(description="Creation timestamp.")


RolePermissionPresetEdge = Edge[RolePermissionPresetGQL]


@gql_connection_type(
    BackendAIGQLMeta(
        added_version="26.4.4",
        description="Paginated connection for role permission preset entries.",
    ),
)
class RolePermissionPresetConnection(Connection[RolePermissionPresetGQL]):
    count: int = gql_field(
        description="Total number of permission entries matching the query criteria."
    )

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count


# --- Filter / Order types ---


@gql_pydantic_input(
    BackendAIGQLMeta(
        description=(
            "Filter input for role permission preset entries. Also used as the input for the "
            "`permission_presets` field resolver on a role preset (the resolver injects "
            "`role_preset_id` from its parent)."
        ),
        added_version="26.4.4",
    ),
    name="RolePermissionPresetFilter",
)
class RolePermissionPresetFilterGQL(PydanticInputMixin[RolePermissionPresetFilterDTO]):
    role_preset_id: UUIDFilter | None = gql_field(
        description="Filter by parent role preset ID.", default=None
    )
    entity_type: RBACElementTypeFilterGQL | None = gql_field(
        description="Filter by entity type the permission applies to.", default=None
    )
    operation: OperationTypeFilterGQL | None = gql_field(
        description="Filter by granted operation.", default=None
    )
    created_at: DateTimeFilter | None = gql_field(
        description="Filter by creation timestamp.", default=None
    )
    AND: list[Self] | None = gql_field(
        description="Combine multiple filters with AND logic. All conditions must match.",
        default=None,
    )
    OR: list[Self] | None = gql_field(
        description="Combine multiple filters with OR logic. At least one condition must match.",
        default=None,
    )
    NOT: list[Self] | None = gql_field(
        description="Negate the specified filters. Matching records are excluded.",
        default=None,
    )


@gql_enum(
    BackendAIGQLMeta(
        added_version="26.4.4",
        description="Fields available for ordering role permission preset entries.",
    ),
    name="RolePermissionPresetOrderField",
)
class RolePermissionPresetOrderFieldGQL(StrEnum):
    ENTITY_TYPE = "entity_type"
    OPERATION = "operation"
    CREATED_AT = "created_at"


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Specifies ordering for role permission preset entries.",
        added_version="26.4.4",
    ),
    name="RolePermissionPresetOrderBy",
)
class RolePermissionPresetOrderByGQL(PydanticInputMixin[RolePermissionPresetOrderDTO]):
    field: RolePermissionPresetOrderFieldGQL = gql_field(description="The field to order by.")
    direction: OrderDirection = gql_field(description="Sort direction.", default=OrderDirection.ASC)


# --- Payload types ---


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.4.4",
        description="Failure detail for a single permission entry in a bulk operation.",
    ),
    model=BulkRolePermissionPresetFailureInfoDTO,
    name="BulkRolePermissionPresetFailureInfo",
)
class BulkRolePermissionPresetFailureInfoGQL(
    PydanticOutputMixin[BulkRolePermissionPresetFailureInfoDTO]
):
    permission_preset_id: UUID = gql_field(
        description="Permission entry ID that the operation failed on."
    )
    message: str = gql_field(description="Error message describing the failure.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.4.4",
        description="Failure detail for a single permission entry in a bulk add operation.",
    ),
    model=BulkAddRolePermissionPresetFailureInfoDTO,
    name="BulkAddRolePermissionPresetFailureInfo",
)
class BulkAddRolePermissionPresetFailureInfoGQL(
    PydanticOutputMixin[BulkAddRolePermissionPresetFailureInfoDTO]
):
    entity_type: RBACElementTypeGQL = gql_field(
        description="Entity type of the permission entry that failed."
    )
    operation: OperationTypeGQL = gql_field(
        description="Operation of the permission entry that failed."
    )
    message: str = gql_field(description="Error message describing the failure.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.4.4",
        description="Payload returned after bulk-adding permission entries to a role preset.",
    ),
    model=BulkAddRolePermissionPresetsPayloadDTO,
    name="BulkAddRolePermissionPresetsPayload",
)
class BulkAddRolePermissionPresetsPayloadGQL(
    PydanticOutputMixin[BulkAddRolePermissionPresetsPayloadDTO]
):
    items: list[RolePermissionPresetGQL] = gql_field(
        description="Permission entries that were added."
    )
    failed: list[BulkAddRolePermissionPresetFailureInfoGQL] = gql_field(
        description="Permission entries that failed to be added (e.g., duplicates)."
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.4.4",
        description="Payload returned after bulk-removing permission entries from a role preset.",
    ),
    model=BulkRemoveRolePermissionPresetsPayloadDTO,
    name="BulkRemoveRolePermissionPresetsPayload",
)
class BulkRemoveRolePermissionPresetsPayloadGQL(
    PydanticOutputMixin[BulkRemoveRolePermissionPresetsPayloadDTO]
):
    items: list[RolePermissionPresetGQL] = gql_field(
        description="Permission entries that were removed."
    )
    failed: list[BulkRolePermissionPresetFailureInfoGQL] = gql_field(
        description="Permission entry IDs that failed to delete."
    )
