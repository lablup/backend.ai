from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import EntityType
from ai.backend.manager.actions.action import BaseAction, BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.permission.permission import PermissionData
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.base.purger import Purger


@dataclass
class PermissionAction(BaseAction):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.PERMISSION


@dataclass
class CreatePermissionAction(PermissionAction):
    creator: Creator[PermissionRow]

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
        return str(self.data.id) if self.data else None


@dataclass
class DeletePermissionAction(PermissionAction):
    purger: Purger[PermissionRow]

    @override
    def entity_id(self) -> str | None:
        return str(self.purger.pk_value)

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
