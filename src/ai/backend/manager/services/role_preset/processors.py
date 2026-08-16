from __future__ import annotations

from ai.backend.manager.actions.registry import ProcessorGroup
from ai.backend.manager.actions.v2.bulk.processor import BulkActionProcessor
from ai.backend.manager.actions.v2.global_scope.processor import GlobalActionProcessor
from ai.backend.manager.actions.v2.ops.result import (
    BatchOpsResult,
    BulkOpsResult,
    CreatedEntityWithFieldsOpsResult,
    EntitiesOpsResult,
    EntityOpsResult,
)
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
from ai.backend.manager.services.role_preset.validators import RoleNameTemplateValidator


class RolePresetProcessors:
    """Every operation runs straight against ops, so this domain has no service.

    Two groups because the domain writes two entities: the preset and the
    permission entries it owns.
    """

    create: GlobalActionProcessor[
        CreateRolePresetAction,
        CreatedEntityWithFieldsOpsResult[RolePresetData, RolePermissionPresetData],
    ]
    get: GlobalActionProcessor[GetRolePresetAction, EntityOpsResult[RolePresetData]]
    search: GlobalActionProcessor[SearchRolePresetsAction, BatchOpsResult[RolePresetData]]
    search_permission_presets: GlobalActionProcessor[
        SearchRolePermissionPresetsAction, BatchOpsResult[RolePermissionPresetData]
    ]
    update: GlobalActionProcessor[UpdateRolePresetAction, EntityOpsResult[RolePresetData]]
    bulk_delete: BulkActionProcessor[BulkDeleteRolePresetsAction, BulkOpsResult[RolePresetData]]
    bulk_restore: BulkActionProcessor[BulkRestoreRolePresetsAction, BulkOpsResult[RolePresetData]]
    purge: SingleEntityActionProcessor[PurgeRolePresetAction, EntityOpsResult[RolePresetData]]
    bulk_purge: BulkActionProcessor[BulkPurgeRolePresetsAction, BulkOpsResult[RolePresetData]]
    bulk_add_permissions: SingleEntityActionProcessor[
        BulkAddRolePermissionPresetsAction, EntitiesOpsResult[RolePermissionPresetData]
    ]
    bulk_remove_permissions: BulkActionProcessor[
        BulkRemoveRolePermissionPresetsAction, BulkOpsResult[RolePermissionPresetData]
    ]

    def __init__(
        self,
        preset_group: ProcessorGroup[RolePresetData],
        permission_group: ProcessorGroup[RolePermissionPresetData],
    ) -> None:
        self.create = preset_group.global_create_with_fields_ops(
            CreateRolePresetAction, validators=[RoleNameTemplateValidator()]
        )
        self.get = preset_group.global_get_ops(GetRolePresetAction)
        self.search = preset_group.global_search_ops(SearchRolePresetsAction)
        self.search_permission_presets = permission_group.global_search_ops(
            SearchRolePermissionPresetsAction
        )
        self.update = preset_group.global_update_ops(
            UpdateRolePresetAction, validators=[RoleNameTemplateValidator()]
        )
        self.bulk_delete = preset_group.partial_bulk_delete_ops(BulkDeleteRolePresetsAction)
        self.bulk_restore = preset_group.partial_bulk_restore_ops(BulkRestoreRolePresetsAction)
        self.purge = preset_group.entity_purge_ops(PurgeRolePresetAction)
        self.bulk_purge = preset_group.global_partial_bulk_purge_ops(BulkPurgeRolePresetsAction)
        self.bulk_add_permissions = permission_group.field_atomic_create_ops(
            BulkAddRolePermissionPresetsAction
        )
        self.bulk_remove_permissions = permission_group.field_partial_bulk_purge_ops(
            BulkRemoveRolePermissionPresetsAction
        )
