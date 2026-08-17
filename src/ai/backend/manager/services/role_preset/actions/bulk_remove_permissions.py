from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.role_permission_preset import RolePermissionPresetID
from ai.backend.common.data.entity.role_preset import RolePresetID
from ai.backend.manager.actions.v2.ops.base import PartialBulkPurgeFieldOpsAction
from ai.backend.manager.data.role_preset.types import RolePermissionPresetData
from ai.backend.manager.models.rbac_models.role_permission_preset.lookups import (
    RolePermissionPresetOwnerLookup,
)
from ai.backend.manager.models.rbac_models.role_permission_preset.purgers import (
    RolePermissionPresetPurger,
)
from ai.backend.manager.models.rbac_models.role_permission_preset.row import (
    RolePermissionPresetRow,
)


@dataclass
class BulkRemoveRolePermissionPresetsAction(
    PartialBulkPurgeFieldOpsAction[
        RolePermissionPresetID,
        RolePresetID,
        RolePermissionPresetRow,
        RolePermissionPresetData,
    ]
):
    """Drop the named permission entries, answering for each one.

    The entries may belong to different presets; every one of those presets answers for
    the removal of the entries it owns.
    """

    ids: Sequence[RolePermissionPresetID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_remove_role_permission_presets"

    @override
    def field_ids(self) -> Sequence[RolePermissionPresetID]:
        return tuple(self.ids)

    @override
    def to_owner_lookup(self) -> RolePermissionPresetOwnerLookup:
        return RolePermissionPresetOwnerLookup()

    @override
    def to_purgers(self) -> Mapping[RolePermissionPresetID, RolePermissionPresetPurger]:
        return {
            permission_id: RolePermissionPresetPurger(permission_preset_id=permission_id)
            for permission_id in self.ids
        }
