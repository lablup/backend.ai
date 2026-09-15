from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.role import RoleID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction
from ai.backend.manager.data.permission.role import RoleDetailData


@dataclass(frozen=True)
class GetRoleDetailAction(BaseSingleEntityAction):
    """Read one role with its permissions and the users it is assigned to."""

    role_id: RoleID

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.role_id

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_role_detail"


@dataclass(frozen=True)
class GetRoleDetailActionResult:
    role: RoleDetailData
