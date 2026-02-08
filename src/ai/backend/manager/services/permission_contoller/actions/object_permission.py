from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import EntityType
from ai.backend.manager.actions.action import BaseAction, BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.permission.object_permission import ObjectPermissionData
from ai.backend.manager.models.rbac_models.permission.object_permission import ObjectPermissionRow
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.base.purger import Purger


@dataclass
class ObjectPermissionAction(BaseAction):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.OBJECT_PERMISSION


@dataclass
class CreateObjectPermissionAction(ObjectPermissionAction):
    creator: Creator[ObjectPermissionRow]

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.OBJECT_PERMISSION

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


@dataclass
class CreateObjectPermissionActionResult(BaseActionResult):
    data: ObjectPermissionData

    @override
    def entity_id(self) -> str | None:
        return str(self.data.id) if self.data else None


@dataclass
class DeleteObjectPermissionAction(ObjectPermissionAction):
    purger: Purger[ObjectPermissionRow]

    @override
    def entity_id(self) -> str | None:
        return str(self.purger.pk_value)

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.OBJECT_PERMISSION

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE


@dataclass
class DeleteObjectPermissionActionResult(BaseActionResult):
    data: ObjectPermissionData | None

    @override
    def entity_id(self) -> str | None:
        return str(self.data.id) if self.data else None
