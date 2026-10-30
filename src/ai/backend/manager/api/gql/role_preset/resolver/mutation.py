"""Role preset GQL mutation resolvers."""

from __future__ import annotations

from uuid import UUID

from strawberry import Info

from ai.backend.common.data.entity.role_preset import RolePresetID
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.base import to_global_id
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_mutation,
)
from ai.backend.manager.api.gql.role_preset.types.inputs import (
    BulkAddRolePermissionPresetsInputGQL,
    BulkDeleteRolePresetsInputGQL,
    BulkPurgeRolePresetsInputGQL,
    BulkRemoveRolePermissionPresetsInputGQL,
    BulkRestoreRolePresetsInputGQL,
    CreateRolePresetInputGQL,
    PartialBulkDeleteRolePresetsInputGQL,
    PartialBulkPurgeRolePresetsInputGQL,
    PartialBulkRemoveRolePresetPermissionsInputGQL,
    PartialBulkRestoreRolePresetsInputGQL,
    PartialBulkUpdateRolePresetsInputGQL,
    UpdateRolePresetBodyInputGQL,
    UpdateRolePresetInputGQL,
)
from ai.backend.manager.api.gql.role_preset.types.node import RolePresetGQL
from ai.backend.manager.api.gql.role_preset.types.payloads import (
    BulkDeleteRolePresetsPayloadGQL,
    BulkPurgeRolePresetsPayloadGQL,
    BulkRestoreRolePresetsPayloadGQL,
    CreateRolePresetPayloadGQL,
    DeleteRolePresetPayloadGQL,
    PartialBulkRolePresetsPayloadGQL,
    PurgeRolePresetPayloadGQL,
    RestoreRolePresetPayloadGQL,
    UpdateRolePresetPayloadGQL,
)
from ai.backend.manager.api.gql.role_preset.types.permission import (
    AtomicBulkAddRolePresetPermissionsPayloadGQL,
    BulkAddRolePermissionPresetsPayloadGQL,
    BulkRemoveRolePermissionPresetsPayloadGQL,
    PartialBulkRolePresetPermissionsPayloadGQL,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only


@gql_mutation(
    BackendAIGQLMeta(
        added_version="26.4.4",
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
        description="Update a role preset's metadata. Only provided fields will be updated.",
    )
)
async def update_role_preset(
    info: Info[StrawberryGQLContext],
    id: UUID,
    input: UpdateRolePresetBodyInputGQL,
) -> UpdateRolePresetPayloadGQL:
    payload = await info.context.adapters.role_preset.update(RolePresetID(id), input.to_pydantic())
    return UpdateRolePresetPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(added_version=NEXT_RELEASE_VERSION, description="Soft-delete a role preset.")
)
async def delete_role_preset(
    info: Info[StrawberryGQLContext],
    id: UUID,
) -> DeleteRolePresetPayloadGQL:
    payload = await info.context.adapters.role_preset.delete(RolePresetID(id))
    return DeleteRolePresetPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION, description="Restore a soft-deleted role preset."
    )
)
async def restore_role_preset(
    info: Info[StrawberryGQLContext],
    id: UUID,
) -> RestoreRolePresetPayloadGQL:
    payload = await info.context.adapters.role_preset.restore(RolePresetID(id))
    return RestoreRolePresetPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Purge a role preset together with its permission entries.",
    )
)
async def purge_role_preset(
    info: Info[StrawberryGQLContext],
    id: UUID,
) -> PurgeRolePresetPayloadGQL:
    payload = await info.context.adapters.role_preset.purge(RolePresetID(id))
    return PurgeRolePresetPayloadGQL.from_pydantic(
        payload, extra={"purged_id": to_global_id(RolePresetGQL, payload.entity_id)}
    )


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Update several role presets, answering for each one.",
    )
)
async def partial_bulk_update_role_presets(
    info: Info[StrawberryGQLContext],
    input: PartialBulkUpdateRolePresetsInputGQL,
) -> PartialBulkRolePresetsPayloadGQL:
    payload = await info.context.adapters.role_preset.partial_bulk_update(input.to_pydantic())
    return PartialBulkRolePresetsPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Soft-delete several role presets, answering for each one.",
    )
)
async def partial_bulk_delete_role_presets(
    info: Info[StrawberryGQLContext],
    input: PartialBulkDeleteRolePresetsInputGQL,
) -> PartialBulkRolePresetsPayloadGQL:
    payload = await info.context.adapters.role_preset.partial_bulk_delete(input.to_pydantic())
    return PartialBulkRolePresetsPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Restore several soft-deleted role presets, answering for each one.",
    )
)
async def partial_bulk_restore_role_presets(
    info: Info[StrawberryGQLContext],
    input: PartialBulkRestoreRolePresetsInputGQL,
) -> PartialBulkRolePresetsPayloadGQL:
    payload = await info.context.adapters.role_preset.partial_bulk_restore(input.to_pydantic())
    return PartialBulkRolePresetsPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Purge several role presets, answering for each one.",
    )
)
async def partial_bulk_purge_role_presets(
    info: Info[StrawberryGQLContext],
    input: PartialBulkPurgeRolePresetsInputGQL,
) -> PartialBulkRolePresetsPayloadGQL:
    payload = await info.context.adapters.role_preset.partial_bulk_purge(input.to_pydantic())
    return PartialBulkRolePresetsPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Add permission entries to an existing role preset, all or none.",
    )
)
async def atomic_bulk_add_role_preset_permissions(
    info: Info[StrawberryGQLContext],
    input: BulkAddRolePermissionPresetsInputGQL,
) -> AtomicBulkAddRolePresetPermissionsPayloadGQL:
    payload = await info.context.adapters.role_preset.atomic_bulk_add_permissions(
        RolePresetID(UUID(str(input.role_preset_id))), input.to_pydantic()
    )
    return AtomicBulkAddRolePresetPermissionsPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Remove several role preset permission entries, answering for each one.",
    )
)
async def partial_bulk_remove_role_preset_permissions(
    info: Info[StrawberryGQLContext],
    input: PartialBulkRemoveRolePresetPermissionsInputGQL,
) -> PartialBulkRolePresetPermissionsPayloadGQL:
    payload = await info.context.adapters.role_preset.partial_bulk_remove_permissions(
        input.to_pydantic()
    )
    return PartialBulkRolePresetPermissionsPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version="26.4.4",
        description="Update an existing role preset's metadata (admin only).",
    ),
    deprecation_reason=f"Deprecated since {NEXT_RELEASE_VERSION}. Use `updateRolePreset`.",
)
async def admin_update_role_preset(
    info: Info[StrawberryGQLContext],
    input: UpdateRolePresetInputGQL,
) -> UpdateRolePresetPayloadGQL | None:
    check_admin_only()
    dto = input.to_pydantic()
    payload = await info.context.adapters.role_preset.update(dto.role_preset_id, dto)
    return UpdateRolePresetPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version="26.4.4",
        description="Bulk-soft-delete role presets (admin only).",
    ),
    deprecation_reason=(
        f"Deprecated since {NEXT_RELEASE_VERSION}. Use `partialBulkDeleteRolePresets`."
    ),
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
        added_version="26.4.4",
        description="Bulk-restore soft-deleted role presets (admin only).",
    ),
    deprecation_reason=(
        f"Deprecated since {NEXT_RELEASE_VERSION}. Use `partialBulkRestoreRolePresets`."
    ),
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
        added_version="26.4.4",
        description="Bulk-hard-delete role presets (admin only).",
    ),
    deprecation_reason=(
        f"Deprecated since {NEXT_RELEASE_VERSION}. Use `partialBulkPurgeRolePresets`."
    ),
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
        added_version="26.4.4",
        description="Bulk-add permission entries to an existing role preset (admin only).",
    ),
    deprecation_reason=(
        f"Deprecated since {NEXT_RELEASE_VERSION}. Use `atomicBulkAddRolePresetPermissions`."
    ),
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
        added_version="26.4.4",
        description="Bulk-remove permission entries from a role preset (admin only).",
    ),
    deprecation_reason=(
        f"Deprecated since {NEXT_RELEASE_VERSION}. Use `partialBulkRemoveRolePresetPermissions`."
    ),
)
async def admin_bulk_remove_role_preset_permissions(
    info: Info[StrawberryGQLContext],
    input: BulkRemoveRolePermissionPresetsInputGQL,
) -> BulkRemoveRolePermissionPresetsPayloadGQL | None:
    check_admin_only()
    payload = await info.context.adapters.role_preset.bulk_remove_permissions(input.to_pydantic())
    return BulkRemoveRolePermissionPresetsPayloadGQL.from_pydantic(payload)
