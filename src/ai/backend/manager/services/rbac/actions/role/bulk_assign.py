import uuid
from dataclasses import dataclass, field
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.permission.role import (
    BulkRoleAssignmentResultData,
)
from ai.backend.manager.models.rbac_models.user_role import UserRoleRow
from ai.backend.manager.repositories.base.creator import BulkCreator
from ai.backend.manager.services.rbac.actions.role.base import RoleAction


@dataclass
class BulkAssignRoleAction(RoleAction):
    bulk_creator: BulkCreator[UserRoleRow]
    project_id: uuid.UUID | None = field(default=None)

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
