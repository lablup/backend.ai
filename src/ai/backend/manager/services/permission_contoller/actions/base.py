from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import EntityType
from ai.backend.manager.actions.action import BaseAction
from ai.backend.manager.actions.action.scope import BaseScopeAction, BaseScopeActionResult


@dataclass
class RoleAction(BaseAction):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.ROLE


@dataclass
class RoleScopeAction(BaseScopeAction):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.ROLE


@dataclass
class RoleScopeActionResult(BaseScopeActionResult):
    pass


@dataclass
class PermissionAction(BaseAction):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.PERMISSION
