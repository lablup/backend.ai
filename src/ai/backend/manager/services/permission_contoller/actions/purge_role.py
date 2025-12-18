from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.permission.role import RoleData
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.repositories.base.purger import Purger
from ai.backend.manager.services.permission_contoller.actions.base import RoleAction


@dataclass
class PurgeRoleAction(RoleAction):
    """Action for permanently removing a role from the database (hard delete)."""

    purger: Purger[RoleRow]

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.purger.pk_value)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "purge"


@dataclass
class PurgeRoleActionResult(BaseActionResult):
    data: RoleData

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.data.id)
