from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import EntityType
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.permission.role import (
    BulkRoleAssignmentResultData,
)
from ai.backend.manager.models.rbac_models.user_role import UserRoleRow
from ai.backend.manager.repositories.base.creator import BulkCreator
from ai.backend.manager.services.permission_contoller.actions.base import RoleAction


@dataclass
class BulkAssignRoleAction(RoleAction):
    bulk_creator: BulkCreator[UserRoleRow]

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.ROLE_ASSIGNMENT

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


@dataclass
class BulkAssignRoleActionResult(BaseActionResult):
    data: BulkRoleAssignmentResultData

    @override
    def entity_id(self) -> str | None:
        return None
