import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.services.group.actions.base import (
    GroupSingleEntityAction,
    GroupSingleEntityActionResult,
)


@dataclass
class PurgeGroupAction(GroupSingleEntityAction):
    group_id: uuid.UUID

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.PURGE

    @override
    def target_entity_id(self) -> str:
        return str(self.group_id)

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.PROJECT, str(self.group_id))


@dataclass
class PurgeGroupActionResult(GroupSingleEntityActionResult):
    group_id: uuid.UUID

    @override
    def target_entity_id(self) -> str:
        return str(self.group_id)
