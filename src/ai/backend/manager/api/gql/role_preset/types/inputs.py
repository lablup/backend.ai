"""Role preset GQL input types."""

from __future__ import annotations

from strawberry import ID, UNSET

from ai.backend.common.dto.manager.v2.role_permission_preset.request import (
    BulkAddRolePermissionPresetsInput as BulkAddRolePermissionPresetsInputDTO,
)
from ai.backend.common.dto.manager.v2.role_permission_preset.request import (
    BulkRemoveRolePermissionPresetsInput as BulkRemoveRolePermissionPresetsInputDTO,
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
    UpdateRolePresetInput as UpdateRolePresetInputDTO,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_field,
    gql_pydantic_input,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticInputMixin
from ai.backend.manager.api.gql.rbac.types import OperationTypeGQL, RBACElementTypeGQL


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="A single (entity_type, operation) pair carried by a role preset.",
        added_version=NEXT_RELEASE_VERSION,
    ),
    name="RolePermissionPresetEntryInput",
)
class RolePermissionPresetEntryInputGQL(PydanticInputMixin[RolePermissionPresetEntryDTO]):
    entity_type: RBACElementTypeGQL = gql_field(
        description="Entity type the permission applies to."
    )
    operation: OperationTypeGQL = gql_field(description="Operation granted by the permission.")


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Input for creating a new role preset.",
        added_version=NEXT_RELEASE_VERSION,
    ),
    name="CreateRolePresetInput",
)
class CreateRolePresetInputGQL(PydanticInputMixin[CreateRolePresetInputDTO]):
    name: str = gql_field(description="Role preset name.")
    scope_type: RBACElementTypeGQL = gql_field(
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
        added_version=NEXT_RELEASE_VERSION,
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
        description="Input for bulk-soft-deleting role presets.",
        added_version=NEXT_RELEASE_VERSION,
    ),
    name="BulkDeleteRolePresetsInput",
)
class BulkDeleteRolePresetsInputGQL(PydanticInputMixin[BulkDeleteRolePresetsInputDTO]):
    role_preset_ids: list[ID] = gql_field(description="Role preset UUIDs to soft-delete.")


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Input for bulk-restoring soft-deleted role presets.",
        added_version=NEXT_RELEASE_VERSION,
    ),
    name="BulkRestoreRolePresetsInput",
)
class BulkRestoreRolePresetsInputGQL(PydanticInputMixin[BulkRestoreRolePresetsInputDTO]):
    role_preset_ids: list[ID] = gql_field(description="Role preset UUIDs to restore.")


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Input for bulk-hard-deleting role presets.",
        added_version=NEXT_RELEASE_VERSION,
    ),
    name="BulkPurgeRolePresetsInput",
)
class BulkPurgeRolePresetsInputGQL(PydanticInputMixin[BulkPurgeRolePresetsInputDTO]):
    role_preset_ids: list[ID] = gql_field(description="Role preset UUIDs to purge.")


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Input for bulk-adding permission entries to an existing role preset.",
        added_version=NEXT_RELEASE_VERSION,
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
        added_version=NEXT_RELEASE_VERSION,
    ),
    name="BulkRemoveRolePermissionPresetsInput",
)
class BulkRemoveRolePermissionPresetsInputGQL(
    PydanticInputMixin[BulkRemoveRolePermissionPresetsInputDTO]
):
    permission_preset_ids: list[ID] = gql_field(description="Permission entry row IDs to delete.")
