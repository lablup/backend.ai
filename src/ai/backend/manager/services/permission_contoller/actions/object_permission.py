from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseAction, BaseActionResult
from ai.backend.manager.data.permission.object_permission import ObjectPermissionData
from ai.backend.manager.models.rbac_models.permission.object_permission import ObjectPermissionRow
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.base.purger import Purger


@dataclass
class ObjectPermissionAction(BaseAction):
    @override
    @classmethod
    def entity_type(cls) -> str:
        return "object_permission"


@dataclass
class CreateObjectPermissionAction(ObjectPermissionAction):
    creator: Creator[ObjectPermissionRow]

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def entity_type(cls) -> str:
        return "object_permission"

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "create"


@dataclass
class CreateObjectPermissionActionResult(BaseActionResult):
    data: ObjectPermissionData

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.data.id) if self.data else None


@dataclass
class DeleteObjectPermissionAction(ObjectPermissionAction):
    purger: Purger[ObjectPermissionRow]

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.purger.pk_value)

    @override
    @classmethod
    def entity_type(cls) -> str:
        return "object_permission"

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "delete"


@dataclass
class DeleteObjectPermissionActionResult(BaseActionResult):
    data: Optional[ObjectPermissionData]

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.data.id) if self.data else None
