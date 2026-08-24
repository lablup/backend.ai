"""Read specs for role permission presets."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, override
from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.data.entity.role_permission_preset import RolePermissionPresetID
from ai.backend.common.data.entity.role_preset import ROLE_PRESET_ENTITY_TYPE, RolePresetID
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.models.rbac_models.role_permission_preset.row import (
    RolePermissionPresetRow,
)
from ai.backend.manager.models.specs.lookup import FieldOwnerLookup


class RolePermissionPresetOwnerLookup(FieldOwnerLookup[RolePermissionPresetID, RolePresetID]):
    """The preset a permission entry belongs to."""

    @override
    def build_query(self, field_ids: Sequence[RolePermissionPresetID]) -> sa.sql.Select[Any]:
        return sa.select(
            RolePermissionPresetRow.id,
            RolePermissionPresetRow.role_preset_id,
            sa.literal(ROLE_PRESET_ENTITY_TYPE),
        ).where(RolePermissionPresetRow.id.in_(field_ids))

    @override
    def to_entity_id(self, value: UUID, owner_type: EntityType) -> RolePresetID:
        return RolePresetID(value)
