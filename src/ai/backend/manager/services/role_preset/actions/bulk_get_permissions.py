from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.role_permission_preset import RolePermissionPresetID
from ai.backend.common.data.entity.role_preset import RolePresetID
from ai.backend.manager.actions.v2.field.ops import PartialBulkGetFieldOpsAction
from ai.backend.manager.data.role_preset.types import RolePermissionPresetData
from ai.backend.manager.models.rbac_models.role_permission_preset.queriers import (
    BulkRolePermissionPresetQuerier,
)
from ai.backend.manager.models.rbac_models.role_permission_preset.row import (
    RolePermissionPresetRow,
)
from ai.backend.manager.services.role_preset.actions.lookup_permission_owner import (
    LookupBulkRolePermissionPresetOwnerAction,
)


@dataclass
class BulkGetRolePermissionPresetsAction(
    PartialBulkGetFieldOpsAction[
        RolePermissionPresetID,
        RolePresetID,
        RolePermissionPresetRow,
        RolePermissionPresetData,
    ]
):
    """Read the preset permission entries the caller named."""

    ids: Sequence[RolePermissionPresetID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_get_role_permission_presets"

    @override
    def field_ids(self) -> Sequence[RolePermissionPresetID]:
        return tuple(self.ids)

    @override
    def to_owner_lookup_action(self) -> LookupBulkRolePermissionPresetOwnerAction:
        return LookupBulkRolePermissionPresetOwnerAction(permission_preset_ids=self.ids)

    @override
    def to_querier(self) -> BulkRolePermissionPresetQuerier:
        return BulkRolePermissionPresetQuerier()

    @override
    def narrowed_to(self, field_ids: Sequence[RolePermissionPresetID]) -> Self:
        allowed = frozenset(field_ids)
        return replace(self, ids=[field_id for field_id in self.ids if field_id in allowed])
