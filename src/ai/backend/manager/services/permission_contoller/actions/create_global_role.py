from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.role import ROLE_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import CreateGlobalOpsAction
from ai.backend.manager.data.permission.role import RoleData
from ai.backend.manager.models.rbac_models.role.creators import GlobalRoleCreator
from ai.backend.manager.models.rbac_models.role.row import RoleRow


@dataclass(frozen=True)
class CreateGlobalRoleAction(CreateGlobalOpsAction[RoleRow, RoleData]):
    """Create a role registered in no scope."""

    creator: GlobalRoleCreator

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return ROLE_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "create_global_role"

    @override
    def to_creator(self) -> GlobalRoleCreator:
        return self.creator
