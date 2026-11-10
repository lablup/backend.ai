from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.role import RoleEntityType
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import ScopedSearchOpsAction
from ai.backend.manager.data.permission.role import RoleData
from ai.backend.manager.models.rbac_models.role.row import RoleRow

__all__ = ("SearchRolesInScopeAction",)


@dataclass(frozen=True)
class SearchRolesInScopeAction(ScopedSearchOpsAction[RoleRow, RoleData]):
    """Read the roles the named scopes reach, combined with OR.

    A role created before the v2 write path has no virtual entity node yet and is
    absent from this answer until BA-7571 backfills one.
    """

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return RoleEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_roles_in_scope"
