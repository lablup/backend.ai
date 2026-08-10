from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.role_preset import ROLE_PERMISSION_PRESET_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.identifier.entity import EntityID
from ai.backend.common.identifier.role_permission_preset import RolePermissionPresetID
from ai.backend.manager.actions.v2.ops.base import PartialBulkPurgeFieldEntityOpsAction
from ai.backend.manager.data.role_preset.types import RolePermissionPresetData
from ai.backend.manager.models.rbac_models.role_permission_preset.purgers import (
    RolePermissionPresetPurger,
)
from ai.backend.manager.models.rbac_models.role_permission_preset.row import (
    RolePermissionPresetRow,
)


@dataclass
class BulkRemoveRolePermissionPresetsAction(
    PartialBulkPurgeFieldEntityOpsAction[RolePermissionPresetRow, RolePermissionPresetData]
):
    """Drop the named permission entries, answering for each one."""

    ids: Sequence[RolePermissionPresetID]

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return ROLE_PERMISSION_PRESET_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_remove_role_permission_presets"

    @override
    def entity_ids(self) -> Sequence[EntityID]:
        return tuple(self.ids)

    @override
    def to_purgers(self) -> Mapping[EntityID, RolePermissionPresetPurger]:
        return {
            permission_id: RolePermissionPresetPurger(permission_preset_id=permission_id)
            for permission_id in self.ids
        }
