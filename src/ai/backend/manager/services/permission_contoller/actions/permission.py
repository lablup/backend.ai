from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseAction, BaseActionResult
from ai.backend.manager.data.permission.permission import PermissionData
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.base.purger import Purger


@dataclass
class PermissionAction(BaseAction):
    @override
    @classmethod
    def entity_type(cls) -> str:
        return "permission"


@dataclass
class CreatePermissionAction(PermissionAction):
    creator: Creator[PermissionRow]

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def entity_type(cls) -> str:
        return "permission"

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "create"


@dataclass
class CreatePermissionActionResult(BaseActionResult):
    data: PermissionData

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.data.id) if self.data else None


@dataclass
class DeletePermissionAction(PermissionAction):
    purger: Purger[PermissionRow]

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.purger.pk_value)

    @override
    @classmethod
    def entity_type(cls) -> str:
        return "permission"

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "delete"


@dataclass
class DeletePermissionActionResult(BaseActionResult):
    data: PermissionData

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.data.id)
