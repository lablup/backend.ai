from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

import sqlalchemy as sa

from ai.backend.common.identifier.role_permission_preset import RolePermissionPresetID
from ai.backend.common.identifier.role_preset import RolePresetID
from ai.backend.manager.models.rbac_models.role_permission_preset.row import (
    RolePermissionPresetRow,
)
from ai.backend.manager.repositories.base.purger import BatchPurgerSpec


@dataclass
class RolePermissionPresetByIDsBatchPurgerSpec(BatchPurgerSpec[RolePermissionPresetRow]):
    """Selects permission rows by id, scoped to a single preset."""

    role_preset_id: RolePresetID
    ids: Sequence[RolePermissionPresetID]

    @override
    def build_subquery(self) -> sa.sql.Select[tuple[RolePermissionPresetRow]]:
        return sa.select(RolePermissionPresetRow).where(
            sa.and_(
                RolePermissionPresetRow.role_preset_id == self.role_preset_id,
                RolePermissionPresetRow.id.in_(self.ids),
            )
        )
