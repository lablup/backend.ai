from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.role import RoleID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import PurgeEntityOpsAction
from ai.backend.manager.data.permission.role import RoleData
from ai.backend.manager.models.rbac_models.role.purgers import RolePurger
from ai.backend.manager.models.rbac_models.role.row import RoleRow


@dataclass(frozen=True)
class PurgeRoleAction(PurgeEntityOpsAction[RoleRow, RoleData]):
    """Remove one role for good."""

    role_id: RoleID

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.role_id

    @override
    @classmethod
    def action_name(cls) -> str:
        return "purge_role"

    @override
    def to_purger(self) -> RolePurger:
        return RolePurger(role_id=self.role_id)
