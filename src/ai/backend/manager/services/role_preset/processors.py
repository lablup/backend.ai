from __future__ import annotations

from ai.backend.common.data.entity.role_permission_preset import (
    RolePermissionPresetFieldType,
)
from ai.backend.manager.actions.registry.field import LookupFieldGroup
from ai.backend.manager.actions.registry.group import ProcessorGroup
from ai.backend.manager.actions.registry.types import FieldGroupMeta
from ai.backend.manager.actions.v2.bulk.partial_processor import PartialBulkActionProcessor
from ai.backend.manager.actions.v2.bulk.processor import BulkActionProcessor
from ai.backend.manager.actions.v2.field.bulk_processor import (
    PartialBulkFieldActionProcessor,
)
from ai.backend.manager.actions.v2.global_scope.processor import GlobalActionProcessor
from ai.backend.manager.actions.v2.ops.result import (
    BatchOpsResult,
    CreatedEntityWithFieldsOpsResult,
    EntityOpsResult,
    FieldsOpsResult,
    ScopedFieldsOpsResult,
)
from ai.backend.manager.actions.v2.scope.processor import ScopeActionProcessor
from ai.backend.manager.actions.v2.single_entity.processor import SingleEntityActionProcessor
from ai.backend.manager.data.role_preset.types import (
    RolePermissionPresetData,
    RolePresetData,
)
from ai.backend.manager.services.role_preset.actions.atomic_bulk_add_permissions import (
    AtomicBulkAddRolePresetPermissionsAction,
)
from ai.backend.manager.services.role_preset.actions.bulk_get import BulkGetRolePresetsAction
from ai.backend.manager.services.role_preset.actions.bulk_get_permissions import (
    BulkGetRolePermissionPresetsAction,
)
from ai.backend.manager.services.role_preset.actions.create import CreateRolePresetAction
from ai.backend.manager.services.role_preset.actions.delete import DeleteRolePresetAction
from ai.backend.manager.services.role_preset.actions.get import GetRolePresetAction
from ai.backend.manager.services.role_preset.actions.lookup_permission_owner import (
    LookupBulkRolePermissionPresetOwnerAction,
    LookupRolePermissionPresetOwnerAction,
)
from ai.backend.manager.services.role_preset.actions.partial_bulk_delete import (
    PartialBulkDeleteRolePresetsAction,
)
from ai.backend.manager.services.role_preset.actions.partial_bulk_purge import (
    PartialBulkPurgeRolePresetsAction,
)
from ai.backend.manager.services.role_preset.actions.partial_bulk_remove_permissions import (
    PartialBulkRemoveRolePresetPermissionsAction,
)
from ai.backend.manager.services.role_preset.actions.partial_bulk_restore import (
    PartialBulkRestoreRolePresetsAction,
)
from ai.backend.manager.services.role_preset.actions.partial_bulk_update import (
    PartialBulkUpdateRolePresetsAction,
)
from ai.backend.manager.services.role_preset.actions.purge import PurgeRolePresetAction
from ai.backend.manager.services.role_preset.actions.restore import RestoreRolePresetAction
from ai.backend.manager.services.role_preset.actions.search import SearchRolePresetsAction
from ai.backend.manager.services.role_preset.actions.search_permission_presets import (
    SearchRolePermissionPresetsAction,
)
from ai.backend.manager.services.role_preset.actions.update import UpdateRolePresetAction
from ai.backend.manager.services.role_preset.service import RolePresetService


class RolePresetProcessors:
    """The template-settling writes and the ones re-deriving the preset's roles go
    through the service; the rest run straight against ops.

    One group: the preset is the entity, and its permission entries are field rows of
    it, wired through the field group the preset's group hands out.
    """

    create: ScopeActionProcessor[
        CreateRolePresetAction,
        CreatedEntityWithFieldsOpsResult[RolePresetData, RolePermissionPresetData],
    ]
    get: SingleEntityActionProcessor[GetRolePresetAction, EntityOpsResult[RolePresetData]]
    bulk_get: PartialBulkActionProcessor[BulkGetRolePresetsAction, RolePresetData]
    search: GlobalActionProcessor[SearchRolePresetsAction, BatchOpsResult[RolePresetData]]
    update: SingleEntityActionProcessor[UpdateRolePresetAction, EntityOpsResult[RolePresetData]]
    delete: SingleEntityActionProcessor[DeleteRolePresetAction, EntityOpsResult[RolePresetData]]
    restore: SingleEntityActionProcessor[RestoreRolePresetAction, EntityOpsResult[RolePresetData]]
    purge: SingleEntityActionProcessor[PurgeRolePresetAction, EntityOpsResult[RolePresetData]]
    partial_bulk_update: PartialBulkActionProcessor[
        PartialBulkUpdateRolePresetsAction, RolePresetData
    ]
    partial_bulk_delete: PartialBulkActionProcessor[
        PartialBulkDeleteRolePresetsAction, RolePresetData
    ]
    partial_bulk_restore: PartialBulkActionProcessor[
        PartialBulkRestoreRolePresetsAction, RolePresetData
    ]
    partial_bulk_purge: PartialBulkActionProcessor[
        PartialBulkPurgeRolePresetsAction, RolePresetData
    ]

    # Permission entries: field rows of a preset, answered for by the preset owning them
    search_permission_presets: BulkActionProcessor[
        SearchRolePermissionPresetsAction, ScopedFieldsOpsResult[RolePermissionPresetData]
    ]
    bulk_get_permissions: PartialBulkFieldActionProcessor[
        BulkGetRolePermissionPresetsAction, RolePermissionPresetData
    ]
    atomic_bulk_add_permissions: SingleEntityActionProcessor[
        AtomicBulkAddRolePresetPermissionsAction, FieldsOpsResult[RolePermissionPresetData]
    ]
    partial_bulk_remove_permissions: PartialBulkFieldActionProcessor[
        PartialBulkRemoveRolePresetPermissionsAction, RolePermissionPresetData
    ]

    def __init__(
        self,
        preset_group: ProcessorGroup[RolePresetData],
        service: RolePresetService,
    ) -> None:
        self.create = preset_group.scope(CreateRolePresetAction, service.create)
        self.get = preset_group.single_get_ops(GetRolePresetAction)
        self.bulk_get = preset_group.partial_bulk_get_ops(BulkGetRolePresetsAction)
        self.search = preset_group.global_searcher_ops(SearchRolePresetsAction)
        self.update = preset_group.single_entity(UpdateRolePresetAction, service.update)
        self.delete = preset_group.single_delete_ops(DeleteRolePresetAction)
        self.restore = preset_group.single_restore_ops(RestoreRolePresetAction)
        self.purge = preset_group.entity_purge_ops(PurgeRolePresetAction)
        self.partial_bulk_update = preset_group.partial_bulk(
            PartialBulkUpdateRolePresetsAction, service.partial_bulk_update
        )
        self.partial_bulk_delete = preset_group.partial_bulk_delete_ops(
            PartialBulkDeleteRolePresetsAction
        )
        self.partial_bulk_restore = preset_group.partial_bulk_restore_ops(
            PartialBulkRestoreRolePresetsAction
        )
        self.partial_bulk_purge = preset_group.entity_partial_bulk_purge_ops(
            PartialBulkPurgeRolePresetsAction
        )

        permissions: LookupFieldGroup[RolePermissionPresetData] = preset_group.field_group(
            FieldGroupMeta(RolePermissionPresetFieldType()),
            RolePermissionPresetData,
            LookupRolePermissionPresetOwnerAction,
            LookupBulkRolePermissionPresetOwnerAction,
        )
        self.search_permission_presets = permissions.atomic_bulk_scoped_search_ops(
            SearchRolePermissionPresetsAction
        )
        self.bulk_get_permissions = permissions.partial_bulk_get_ops(
            BulkGetRolePermissionPresetsAction
        )
        self.atomic_bulk_add_permissions = preset_group.single_entity(
            AtomicBulkAddRolePresetPermissionsAction, service.atomic_bulk_add_permissions
        )
        self.partial_bulk_remove_permissions = permissions.partial_bulk_field(
            PartialBulkRemoveRolePresetPermissionsAction, service.partial_bulk_remove_permissions
        )
