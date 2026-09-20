from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.role import RoleEntityType
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import GlobalSearcherOpsAction
from ai.backend.manager.data.permission.role import RoleData
from ai.backend.manager.models.rbac_models.role.row import RoleRow


@dataclass(frozen=True)
class GlobalSearchRolesAction(GlobalSearcherOpsAction[RoleRow, RoleData]):
    """Page through every role, whichever scope it hangs on."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return RoleEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_search_roles"
