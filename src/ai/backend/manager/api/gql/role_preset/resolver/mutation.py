"""Role preset GQL mutation resolvers."""

from __future__ import annotations

from uuid import UUID

from strawberry import Info

from ai.backend.common.identifier.role_preset import RolePresetID
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_mutation,
)
from ai.backend.manager.api.gql.role_preset.types import (
    BulkAddRolePermissionPresetsInputGQL,
    BulkAddRolePermissionPresetsPayloadGQL,
    BulkDeleteRolePresetsInputGQL,
    BulkDeleteRolePresetsPayloadGQL,
    BulkPurgeRolePresetsInputGQL,
    BulkPurgeRolePresetsPayloadGQL,
    BulkRemoveRolePermissionPresetsInputGQL,
    BulkRemoveRolePermissionPresetsPayloadGQL,
    BulkRestoreRolePresetsInputGQL,
    BulkRestoreRolePresetsPayloadGQL,
    CreateRolePresetInputGQL,
    CreateRolePresetPayloadGQL,
    UpdateRolePresetInputGQL,
    UpdateRolePresetPayloadGQL,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Create a new role preset (admin only).",
    )
)
async def admin_create_role_preset(
    info: Info[StrawberryGQLContext],
    input: CreateRolePresetInputGQL,
) -> CreateRolePresetPayloadGQL | None:
    check_admin_only()
    payload = await info.context.adapters.role_preset.create(input.to_pydantic())
    return CreateRolePresetPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Update an existing role preset's metadata (admin only).",
    )
)
async def admin_update_role_preset(
    info: Info[StrawberryGQLContext],
    input: UpdateRolePresetInputGQL,
) -> UpdateRolePresetPayloadGQL | None:
    check_admin_only()
    payload = await info.context.adapters.role_preset.update(input.to_pydantic())
    return UpdateRolePresetPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Bulk-soft-delete role presets (admin only).",
    )
)
async def admin_delete_role_presets(
    info: Info[StrawberryGQLContext],
    input: BulkDeleteRolePresetsInputGQL,
) -> BulkDeleteRolePresetsPayloadGQL | None:
    check_admin_only()
    payload = await info.context.adapters.role_preset.bulk_delete(input.to_pydantic())
    return BulkDeleteRolePresetsPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Bulk-restore soft-deleted role presets (admin only).",
    )
)
async def admin_restore_role_presets(
    info: Info[StrawberryGQLContext],
    input: BulkRestoreRolePresetsInputGQL,
) -> BulkRestoreRolePresetsPayloadGQL | None:
    check_admin_only()
    payload = await info.context.adapters.role_preset.bulk_restore(input.to_pydantic())
    return BulkRestoreRolePresetsPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Bulk-hard-delete role presets (admin only).",
    )
)
async def admin_purge_role_presets(
    info: Info[StrawberryGQLContext],
    input: BulkPurgeRolePresetsInputGQL,
) -> BulkPurgeRolePresetsPayloadGQL | None:
    check_admin_only()
    payload = await info.context.adapters.role_preset.bulk_purge(input.to_pydantic())
    return BulkPurgeRolePresetsPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Bulk-add permission entries to an existing role preset (admin only).",
    )
)
async def admin_bulk_add_role_preset_permissions(
    info: Info[StrawberryGQLContext],
    input: BulkAddRolePermissionPresetsInputGQL,
) -> BulkAddRolePermissionPresetsPayloadGQL | None:
    check_admin_only()
    role_preset_id = RolePresetID(UUID(str(input.role_preset_id)))
    payload = await info.context.adapters.role_preset.bulk_add_permissions(
        role_preset_id, input.to_pydantic()
    )
    return BulkAddRolePermissionPresetsPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Bulk-remove permission entries from a role preset (admin only).",
    )
)
async def admin_bulk_remove_role_preset_permissions(
    info: Info[StrawberryGQLContext],
    input: BulkRemoveRolePermissionPresetsInputGQL,
) -> BulkRemoveRolePermissionPresetsPayloadGQL | None:
    check_admin_only()
    payload = await info.context.adapters.role_preset.bulk_remove_permissions(input.to_pydantic())
    return BulkRemoveRolePermissionPresetsPayloadGQL.from_pydantic(payload)
