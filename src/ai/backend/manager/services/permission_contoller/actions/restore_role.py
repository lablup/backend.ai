from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import RestoreSingleEntityOpsAction
from ai.backend.manager.data.permission.role import RoleData
from ai.backend.manager.models.rbac_models.role.row import RoleRow
from ai.backend.manager.models.specs.soft_delete import RestoreUpdater


@dataclass(frozen=True)
class RestoreRoleAction(RestoreSingleEntityOpsAction[RoleRow, RoleData]):
    """Put one retired role back in service."""

    updater: RestoreUpdater[RoleRow, RoleData]

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.updater.target_id

    @override
    @classmethod
    def action_name(cls) -> str:
        return "restore_role"

    @override
    def to_updater(self) -> RestoreUpdater[RoleRow, RoleData]:
        return self.updater
