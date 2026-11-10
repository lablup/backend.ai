from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import UpdateSingleEntityOpsAction
from ai.backend.manager.data.permission.role import RoleData
from ai.backend.manager.models.rbac_models.role.row import RoleRow
from ai.backend.manager.models.rbac_models.role.updaters import RoleUpdater


@dataclass(frozen=True)
class UpdateRoleAction(UpdateSingleEntityOpsAction[RoleRow, RoleData]):
    """Edit one role's declaration."""

    updater: RoleUpdater

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.updater.role_id

    @override
    @classmethod
    def action_name(cls) -> str:
        return "update_role"

    @override
    def to_updater(self) -> RoleUpdater:
        return self.updater
