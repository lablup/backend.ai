from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.role import RoleEntityType
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import GlobalSearcherOpsAction
from ai.backend.manager.data.permission.permission import PermissionData
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow


@dataclass(frozen=True)
class GlobalSearchPermissionsAction(GlobalSearcherOpsAction[PermissionRow, PermissionData]):
    """Page through every permission entry, whichever role holds it."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return RoleEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_search_permissions"
