"""Role preset GQL mutation resolvers.

Function bodies raise ``NotImplementedError``; wire-up to the adapter/service
layer happens in a follow-up task.
"""

from __future__ import annotations

from strawberry import ID, Info

from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_mutation,
)
from ai.backend.manager.api.gql.role_preset.types import (
    BulkAddRolePermissionPresetsInputGQL,
    BulkAddRolePermissionPresetsPayloadGQL,
    BulkPurgeRolePresetsInputGQL,
    BulkPurgeRolePresetsPayloadGQL,
    BulkRemoveRolePermissionPresetsInputGQL,
    BulkRemoveRolePermissionPresetsPayloadGQL,
    CreateRolePresetInputGQL,
    CreateRolePresetPayloadGQL,
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
    raise NotImplementedError


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
    raise NotImplementedError


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Bulk-add permission entries to an existing role preset (admin only).",
    )
)
async def admin_bulk_add_role_preset_permissions(
    info: Info[StrawberryGQLContext],
    role_preset_id: ID,
    input: BulkAddRolePermissionPresetsInputGQL,
) -> BulkAddRolePermissionPresetsPayloadGQL | None:
    check_admin_only()
    raise NotImplementedError


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
    raise NotImplementedError
