from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import DeleteSingleEntityGuardedOpsAction
from ai.backend.manager.data.permission.role import RoleData
from ai.backend.manager.models.rbac_models.role.row import RoleRow
from ai.backend.manager.models.rbac_models.role.updaters import RoleSoftDeleteUpdater


@dataclass(frozen=True)
class DeleteRoleAction(DeleteSingleEntityGuardedOpsAction[RoleRow, RoleData]):
    """Retire one role."""

    updater: RoleSoftDeleteUpdater

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.updater.role_id

    @override
    @classmethod
    def action_name(cls) -> str:
        return "delete_role"

    @override
    def to_updater(self) -> RoleSoftDeleteUpdater:
        return self.updater
