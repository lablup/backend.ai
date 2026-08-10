from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.role_preset import ROLE_PRESET_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.identifier.entity import EntityID
from ai.backend.common.identifier.role_preset import RolePresetID
from ai.backend.manager.actions.v2.ops.base import PartialBulkPurgeGlobalEntityOpsAction
from ai.backend.manager.data.role_preset.types import RolePresetData
from ai.backend.manager.models.rbac_models.role_preset.purgers import RolePresetPurger
from ai.backend.manager.models.rbac_models.role_preset.row import (
    RolePresetRow,
)


@dataclass
class BulkPurgeRolePresetsAction(
    PartialBulkPurgeGlobalEntityOpsAction[RolePresetRow, RolePresetData]
):
    """Remove the named presets for good, answering for each one."""

    ids: Sequence[RolePresetID]

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return ROLE_PRESET_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_purge_role_presets"

    @override
    def entity_ids(self) -> Sequence[EntityID]:
        return tuple(self.ids)

    @override
    def to_purgers(self) -> Mapping[EntityID, RolePresetPurger]:
        return {preset_id: RolePresetPurger(preset_id=preset_id) for preset_id in self.ids}
