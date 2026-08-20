from __future__ import annotations

from ai.backend.manager.actions.registry.field import FieldProcessorGroup
from ai.backend.manager.actions.registry.group import ProcessorGroup
from ai.backend.manager.actions.v2.bulk.processor import BulkActionProcessor
from ai.backend.manager.actions.v2.field.bulk_processor import BulkFieldActionProcessor
from ai.backend.manager.actions.v2.global_scope.processor import GlobalActionProcessor
from ai.backend.manager.actions.v2.ops.result import (
    BatchOpsResult,
    BulkOpsResult,
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
from ai.backend.manager.services.role_preset.actions.bulk_add_permissions import (
    BulkAddRolePermissionPresetsAction,
)
from ai.backend.manager.services.role_preset.actions.bulk_purge import (
    BulkPurgeRolePresetsAction,
)
from ai.backend.manager.services.role_preset.actions.bulk_remove_permissions import (
    BulkRemoveRolePermissionPresetsAction,
)
from ai.backend.manager.services.role_preset.actions.create import CreateRolePresetAction
from ai.backend.manager.services.role_preset.actions.delete import (
    BulkDeleteRolePresetsAction,
)
from ai.backend.manager.services.role_preset.actions.get import GetRolePresetAction
from ai.backend.manager.services.role_preset.actions.purge import PurgeRolePresetAction
from ai.backend.manager.services.role_preset.actions.restore import (
    BulkRestoreRolePresetsAction,
)
from ai.backend.manager.services.role_preset.actions.search import SearchRolePresetsAction
from ai.backend.manager.services.role_preset.actions.search_permission_presets import (
    SearchRolePermissionPresetsAction,
)
from ai.backend.manager.services.role_preset.actions.update import UpdateRolePresetAction
from ai.backend.manager.services.role_preset.service import RolePresetService


class RolePresetProcessors:
    """The two template-settling writes go through the service; the rest run straight
    against ops.

    One group: the preset is the entity, and its permission entries are field rows of
    it, wired through the field group the preset's group hands out.
    """

    create: GlobalActionProcessor[
        CreateRolePresetAction,
        CreatedEntityWithFieldsOpsResult[RolePresetData, RolePermissionPresetData],
    ]
    get: SingleEntityActionProcessor[GetRolePresetAction, EntityOpsResult[RolePresetData]]
    search: GlobalActionProcessor[SearchRolePresetsAction, BatchOpsResult[RolePresetData]]
    update: SingleEntityActionProcessor[UpdateRolePresetAction, EntityOpsResult[RolePresetData]]
    bulk_delete: BulkActionProcessor[BulkDeleteRolePresetsAction, BulkOpsResult[RolePresetData]]
    bulk_restore: BulkActionProcessor[BulkRestoreRolePresetsAction, BulkOpsResult[RolePresetData]]
    purge: SingleEntityActionProcessor[PurgeRolePresetAction, EntityOpsResult[RolePresetData]]
    bulk_purge: BulkActionProcessor[BulkPurgeRolePresetsAction, BulkOpsResult[RolePresetData]]

    # Permission entries: field rows of a preset, answered for by the preset owning them
    search_permission_presets: ScopeActionProcessor[
        SearchRolePermissionPresetsAction, ScopedFieldsOpsResult[RolePermissionPresetData]
    ]
    bulk_add_permissions: SingleEntityActionProcessor[
        BulkAddRolePermissionPresetsAction, FieldsOpsResult[RolePermissionPresetData]
    ]
    bulk_remove_permissions: BulkFieldActionProcessor[
        BulkRemoveRolePermissionPresetsAction, RolePermissionPresetData
    ]

    def __init__(
        self,
        preset_group: ProcessorGroup[RolePresetData],
        permissions: FieldProcessorGroup[RolePermissionPresetData],
        service: RolePresetService,
    ) -> None:
        self.create = preset_group.global_scope(CreateRolePresetAction, service.create)
        self.get = preset_group.single_get_ops(GetRolePresetAction)
        self.search = preset_group.global_search_ops(SearchRolePresetsAction)
        self.update = preset_group.single_entity(UpdateRolePresetAction, service.update)
        self.bulk_delete = preset_group.partial_bulk_delete_ops(BulkDeleteRolePresetsAction)
        self.bulk_restore = preset_group.partial_bulk_restore_ops(BulkRestoreRolePresetsAction)
        self.purge = preset_group.entity_purge_ops(PurgeRolePresetAction)
        self.bulk_purge = preset_group.global_partial_bulk_purge_ops(BulkPurgeRolePresetsAction)

        self.search_permission_presets = permissions.search_ops(SearchRolePermissionPresetsAction)
        self.bulk_add_permissions = permissions.atomic_create_ops(
            BulkAddRolePermissionPresetsAction
        )
        self.bulk_remove_permissions = permissions.partial_bulk_purge_ops(
            BulkRemoveRolePermissionPresetsAction
        )
