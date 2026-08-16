from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.role_preset import ROLE_PERMISSION_PRESET_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.identifier.entity import EntityID
from ai.backend.common.identifier.role_preset import RolePresetID
from ai.backend.manager.actions.v2.ops.base import AtomicCreateFieldEntityOpsAction
from ai.backend.manager.data.role_preset.types import RolePermissionPresetData
from ai.backend.manager.models.rbac_models.role_permission_preset.creators import (
    RolePermissionPresetCreator,
)
from ai.backend.manager.models.rbac_models.role_permission_preset.row import (
    RolePermissionPresetRow,
)


@dataclass
class BulkAddRolePermissionPresetsAction(
    AtomicCreateFieldEntityOpsAction[
        RolePresetID, RolePermissionPresetRow, RolePermissionPresetData
    ]
):
    """Add permission entries to one preset, all or none.

    Single-entity shaped: the target is the preset, not the entries, which have no id
    until they exist. Atomic because a preset granting a subset is worse than one that
    refused.
    """

    preset_id: RolePresetID
    creators: Sequence[RolePermissionPresetCreator]

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return ROLE_PERMISSION_PRESET_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_add_role_permission_presets"

    @override
    def entity_id(self) -> EntityID:
        return self.preset_id

    @override
    def owner_id(self) -> RolePresetID:
        return self.preset_id

    @override
    def to_creators(self) -> Sequence[RolePermissionPresetCreator]:
        return self.creators
