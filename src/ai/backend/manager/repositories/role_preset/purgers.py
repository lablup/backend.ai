from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.manager.models.rbac_models.role_permission_preset.row import (
    RolePermissionPresetRow,
)
from ai.backend.manager.models.rbac_models.role_preset.row import RolePresetRow
from ai.backend.manager.repositories.base.purger import PurgerSpec
from ai.backend.manager.repositories.base.types import ConflictCheck


@dataclass
class RolePresetPurgerSpec(PurgerSpec[RolePresetRow]):
    """PurgerSpec for deleting a role preset."""

    preset_id: uuid.UUID

    @override
    def row_class(self) -> type[RolePresetRow]:
        return RolePresetRow

    @override
    def pk_value(self) -> uuid.UUID:
        return self.preset_id

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()


@dataclass
class RolePermissionPresetPurgerSpec(PurgerSpec[RolePermissionPresetRow]):
    """PurgerSpec for deleting a role permission preset."""

    permission_preset_id: uuid.UUID

    @override
    def row_class(self) -> type[RolePermissionPresetRow]:
        return RolePermissionPresetRow

    @override
    def pk_value(self) -> uuid.UUID:
        return self.permission_preset_id

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()
