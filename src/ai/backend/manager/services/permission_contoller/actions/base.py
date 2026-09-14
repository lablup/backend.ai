from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.role import RoleEntityType
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.action import BaseAction


@dataclass
class RoleAction(BaseAction):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return RoleEntityType()


@dataclass
class PermissionAction(BaseAction):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.from_name("permission")
