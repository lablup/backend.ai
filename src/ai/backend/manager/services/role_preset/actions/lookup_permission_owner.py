from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.role_permission_preset import RolePermissionPresetID
from ai.backend.common.data.entity.role_preset import ROLE_PRESET_ENTITY_TYPE, RolePresetID
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.field.lookup import LookupFieldOwnerOpsAction
from ai.backend.manager.actions.v2.lookup.base import LookupKey
from ai.backend.manager.models.rbac_models.role_permission_preset.lookups import (
    RolePermissionPresetOwnerLookup,
)


@dataclass(frozen=True)
class RolePermissionPresetIDLookupKey(LookupKey):
    """A permission entry's id, resolved into the preset that owns it."""

    permission_preset_id: RolePermissionPresetID

    @override
    def kind(self) -> str:
        return "role_permission_preset_id"

    @override
    def to_dict(self) -> dict[str, Any]:
        return {"id": str(self.permission_preset_id)}


@dataclass
class LookupRolePermissionPresetOwnerAction(
    LookupFieldOwnerOpsAction[RolePermissionPresetID, RolePresetID]
):
    """The preset a permission entry belongs to."""

    permission_preset_id: RolePermissionPresetID

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return ROLE_PRESET_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "lookup_role_permission_preset_owner"

    @override
    def lookup_key(self) -> LookupKey:
        return RolePermissionPresetIDLookupKey(self.permission_preset_id)

    @override
    def field_id(self) -> RolePermissionPresetID:
        return self.permission_preset_id

    @override
    def to_owner_lookup(self) -> RolePermissionPresetOwnerLookup:
        return RolePermissionPresetOwnerLookup()
