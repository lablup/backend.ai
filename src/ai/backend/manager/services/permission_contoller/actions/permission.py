from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.role import RoleID
from ai.backend.common.data.permission.types import EntityType
from ai.backend.manager.actions.action import BaseAction, BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.permission.permission import PermissionData
from ai.backend.manager.models.rbac_models.permission.creators import RolePermissionCreator
from ai.backend.manager.models.rbac_models.permission.purgers import RolePermissionPurger


@dataclass
class PermissionAction(BaseAction):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.PERMISSION


@dataclass
class CreatePermissionAction(PermissionAction):
    role_id: RoleID
    creator: RolePermissionCreator

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.PERMISSION

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


@dataclass
class CreatePermissionActionResult(BaseActionResult):
    data: PermissionData

    @override
    def entity_id(self) -> str | None:
        return str(self.data.id)


@dataclass
class DeletePermissionAction(PermissionAction):
    purger: RolePermissionPurger

    @override
    def entity_id(self) -> str | None:
        return str(self.purger.target_id_value())

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.PERMISSION

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE


@dataclass
class DeletePermissionActionResult(BaseActionResult):
    data: PermissionData

    @override
    def entity_id(self) -> str | None:
        return str(self.data.id)
