"""Role preset GQL input types."""

from __future__ import annotations

from uuid import UUID

from strawberry import ID, UNSET

from ai.backend.common.dto.manager.v2.role_permission_preset.request import (
    BulkAddRolePermissionPresetsInput as BulkAddRolePermissionPresetsInputDTO,
)
from ai.backend.common.dto.manager.v2.role_permission_preset.request import (
    BulkRemoveRolePermissionPresetsInput as BulkRemoveRolePermissionPresetsInputDTO,
)
from ai.backend.common.dto.manager.v2.role_permission_preset.request import (
    PartialBulkRemoveRolePresetPermissionsInput as PartialBulkRemoveRolePresetPermissionsInputDTO,
)
from ai.backend.common.dto.manager.v2.role_permission_preset.types import (
    RolePermissionPresetEntry as RolePermissionPresetEntryDTO,
)
from ai.backend.common.dto.manager.v2.role_preset.request import (
    BulkDeleteRolePresetsInput as BulkDeleteRolePresetsInputDTO,
)
from ai.backend.common.dto.manager.v2.role_preset.request import (
    BulkPurgeRolePresetsInput as BulkPurgeRolePresetsInputDTO,
)
from ai.backend.common.dto.manager.v2.role_preset.request import (
    BulkRestoreRolePresetsInput as BulkRestoreRolePresetsInputDTO,
)
from ai.backend.common.dto.manager.v2.role_preset.request import (
    CreateRolePresetInput as CreateRolePresetInputDTO,
)
from ai.backend.common.dto.manager.v2.role_preset.request import (
    PartialBulkDeleteRolePresetsInput as PartialBulkDeleteRolePresetsInputDTO,
)
from ai.backend.common.dto.manager.v2.role_preset.request import (
    PartialBulkPurgeRolePresetsInput as PartialBulkPurgeRolePresetsInputDTO,
)
from ai.backend.common.dto.manager.v2.role_preset.request import (
    PartialBulkRestoreRolePresetsInput as PartialBulkRestoreRolePresetsInputDTO,
)
from ai.backend.common.dto.manager.v2.role_preset.request import (
    PartialBulkUpdateRolePresetItemInput as PartialBulkUpdateRolePresetItemInputDTO,
)
from ai.backend.common.dto.manager.v2.role_preset.request import (
    PartialBulkUpdateRolePresetsInput as PartialBulkUpdateRolePresetsInputDTO,
)
from ai.backend.common.dto.manager.v2.role_preset.request import (
    UpdateRolePresetBody as UpdateRolePresetBodyDTO,
)
from ai.backend.common.dto.manager.v2.role_preset.request import (
    UpdateRolePresetInput as UpdateRolePresetInputDTO,
)
from ai.backend.common.dto.manager.v2.role_preset.types import (
    RolePresetUsage as RolePresetUsageDTO,
)
from ai.backend.common.dto.manager.v2.role_preset.types import (
    RolePresetUsedBy as RolePresetUsedByDTO,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_field,
    gql_pydantic_input,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticInputMixin
from ai.backend.manager.api.gql.rbac.types.permission import OperationTypeGQL
from ai.backend.manager.api.gql.rbac.types.scope import PermissionBitGQL


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="A single (entity_type, permission) pair carried by a role preset.",
        added_version="26.4.4",
    ),
    name="RolePermissionPresetEntryInput",
)
class RolePermissionPresetEntryInputGQL(PydanticInputMixin[RolePermissionPresetEntryDTO]):
    entity_type: str = gql_field(description="Entity type the permission applies to.")
    permission: PermissionBitGQL = gql_field(description="The operation bit the entry grants.")
    operation: OperationTypeGQL | None = gql_field(
        description="Operation granted by the permission.",
        default=None,
        deprecation_reason=("Deprecated since 26.9.0. Use `permission`; the value is ignored."),
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Input for creating a new role preset.",
        added_version="26.4.4",
    ),
    name="CreateRolePresetInput",
)
class CreateRolePresetInputGQL(PydanticInputMixin[CreateRolePresetInputDTO]):
    name: str = gql_field(description="Role preset name.")
    scope_type: str = gql_field(
        description="Scope type this preset targets (e.g., domain, project)."
    )
    auto_assign: bool = gql_field(
        description=(
            "Default value for the `auto_assign` flag on roles instantiated from this preset."
        ),
        default=False,
    )
    permissions: list[RolePermissionPresetEntryInputGQL] = gql_field(
        description="Permission entries carried by the preset.",
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        description=(
            "Input for updating a role preset's metadata. Permission entries are managed via the "
            "dedicated add/remove mutations; the `deleted` flag via delete/restore mutations."
        ),
        added_version="26.4.4",
    ),
    name="UpdateRolePresetInput",
)
class UpdateRolePresetInputGQL(PydanticInputMixin[UpdateRolePresetInputDTO]):
    role_preset_id: ID = gql_field(description="Role preset UUID to update.")
    name: str | None = gql_field(description="Updated name.", default=UNSET)
    auto_assign: bool | None = gql_field(
        description="Updated default value for the `auto_assign` flag of instantiated roles.",
        default=UNSET,
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Fields to update on a role preset. Permission entries are managed via the "
            "dedicated add/remove mutations; the `deleted` flag via delete/restore mutations."
        ),
    ),
    name="UpdateRolePresetBodyInput",
)
class UpdateRolePresetBodyInputGQL(PydanticInputMixin[UpdateRolePresetBodyDTO]):
    name: str | None = gql_field(description="Updated name.", default=UNSET)
    auto_assign: bool | None = gql_field(
        description="Updated default value for the `auto_assign` flag of instantiated roles.",
        default=UNSET,
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="One role preset of a partial bulk update and the fields to update on it.",
    ),
    name="PartialBulkUpdateRolePresetItemInput",
)
class PartialBulkUpdateRolePresetItemInputGQL(
    PydanticInputMixin[PartialBulkUpdateRolePresetItemInputDTO]
):
    id: UUID = gql_field(description="ID of the role preset to update.")
    input: UpdateRolePresetBodyInputGQL = gql_field(
        description="Fields to update on the role preset."
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Input for updating several role presets, each answered for separately.",
    ),
    name="PartialBulkUpdateRolePresetsInput",
)
class PartialBulkUpdateRolePresetsInputGQL(
    PydanticInputMixin[PartialBulkUpdateRolePresetsInputDTO]
):
    items: list[PartialBulkUpdateRolePresetItemInputGQL] = gql_field(
        description="The role presets to update, each with its fields."
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Input for soft-deleting several role presets, each answered for separately.",
    ),
    name="PartialBulkDeleteRolePresetsInput",
)
class PartialBulkDeleteRolePresetsInputGQL(
    PydanticInputMixin[PartialBulkDeleteRolePresetsInputDTO]
):
    ids: list[UUID] = gql_field(description="IDs of the role presets to soft-delete.")


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Input for restoring several soft-deleted role presets, each answered for separately."
        ),
    ),
    name="PartialBulkRestoreRolePresetsInput",
)
class PartialBulkRestoreRolePresetsInputGQL(
    PydanticInputMixin[PartialBulkRestoreRolePresetsInputDTO]
):
    ids: list[UUID] = gql_field(description="IDs of the role presets to restore.")


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Input for purging several role presets, each answered for separately.",
    ),
    name="PartialBulkPurgeRolePresetsInput",
)
class PartialBulkPurgeRolePresetsInputGQL(PydanticInputMixin[PartialBulkPurgeRolePresetsInputDTO]):
    ids: list[UUID] = gql_field(description="IDs of the role presets to purge.")


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Input for bulk-soft-deleting role presets.",
        added_version="26.4.4",
    ),
    name="BulkDeleteRolePresetsInput",
)
class BulkDeleteRolePresetsInputGQL(PydanticInputMixin[BulkDeleteRolePresetsInputDTO]):
    role_preset_ids: list[ID] = gql_field(description="Role preset UUIDs to soft-delete.")


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Input for bulk-restoring soft-deleted role presets.",
        added_version="26.4.4",
    ),
    name="BulkRestoreRolePresetsInput",
)
class BulkRestoreRolePresetsInputGQL(PydanticInputMixin[BulkRestoreRolePresetsInputDTO]):
    role_preset_ids: list[ID] = gql_field(description="Role preset UUIDs to restore.")


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Input for bulk-hard-deleting role presets.",
        added_version="26.4.4",
    ),
    name="BulkPurgeRolePresetsInput",
)
class BulkPurgeRolePresetsInputGQL(PydanticInputMixin[BulkPurgeRolePresetsInputDTO]):
    role_preset_ids: list[ID] = gql_field(description="Role preset UUIDs to purge.")


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Input for bulk-adding permission entries to an existing role preset.",
        added_version="26.4.4",
    ),
    name="BulkAddRolePermissionPresetsInput",
)
class BulkAddRolePermissionPresetsInputGQL(
    PydanticInputMixin[BulkAddRolePermissionPresetsInputDTO]
):
    role_preset_id: ID = gql_field(description="ID of the role preset to add permissions to.")
    permissions: list[RolePermissionPresetEntryInputGQL] = gql_field(
        description="Permission entries to insert. Duplicates are surfaced as failures."
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Input for bulk-removing permission entries from a role preset.",
        added_version="26.4.4",
    ),
    name="BulkRemoveRolePermissionPresetsInput",
)
class BulkRemoveRolePermissionPresetsInputGQL(
    PydanticInputMixin[BulkRemoveRolePermissionPresetsInputDTO]
):
    permission_preset_ids: list[ID] = gql_field(description="Permission entry row IDs to delete.")


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Input for removing several role preset permission entries, each answered for "
            "separately."
        ),
    ),
    name="PartialBulkRemoveRolePresetPermissionsInput",
)
class PartialBulkRemoveRolePresetPermissionsInputGQL(
    PydanticInputMixin[PartialBulkRemoveRolePresetPermissionsInputDTO]
):
    ids: list[UUID] = gql_field(description="IDs of the permission entries to remove.")


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Entities whose use of a role preset narrows the read.",
        added_version="26.9.0",
    ),
    name="RolePresetUsedBy",
)
class RolePresetUsedByGQL(PydanticInputMixin[RolePresetUsedByDTO]):
    """The entities whose use of a role preset narrows the read."""

    role: list[ID] | None = gql_field(
        default=None, description="Roles instantiated from the preset."
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        description=(
            "Uses narrowing a role preset query; every id is AND-ed. The caller must be able "
            "to read each listed entity, or the request is refused. Only presets the caller "
            "can read are returned, even when a listed entity is tied to others."
        ),
        added_version="26.9.0",
    ),
    name="RolePresetUsage",
)
class RolePresetUsageGQL(PydanticInputMixin[RolePresetUsageDTO]):
    """The uses that narrow a role preset read."""

    used_by: RolePresetUsedByGQL | None = gql_field(
        default=None, description="Entities whose use of the preset narrows the read."
    )
