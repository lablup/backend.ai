from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.role import RoleEntityType
from ai.backend.common.data.entity.types import EntityType, ScopeRef, ScopeType
from ai.backend.manager.actions.v2.ops.base import CreateEntityOpsAction
from ai.backend.manager.data.permission.role import RoleData
from ai.backend.manager.models.rbac_models.role.creators import RoleCreator
from ai.backend.manager.models.rbac_models.role.row import RoleRow


@dataclass(frozen=True)
class CreateRoleAction(CreateEntityOpsAction[RoleRow, RoleData]):
    """Create a role registered in the scopes the creator names."""

    creator: RoleCreator

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return RoleEntityType()

    @override
    def scope_targets(self) -> Sequence[ScopeRef]:
        scope = self.creator.scope
        return (ScopeRef(scope_type=ScopeType(scope.entity_type()), scope_id=scope),)

    @override
    @classmethod
    def action_name(cls) -> str:
        return "create_role"

    @override
    def to_creator(self) -> RoleCreator:
        return self.creator
