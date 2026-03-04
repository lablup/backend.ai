import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.data.session.types import SessionData
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.services.session.base import SessionSingleEntityAction


@dataclass
class ModifySessionAction(SessionSingleEntityAction):
    """Modify a specific session.

    RBAC validation checks if the user has UPDATE permission for this session.
    """

    session_id: uuid.UUID
    updater: Updater[SessionRow]

    @override
    def entity_id(self) -> str | None:
        return str(self.session_id)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    def target_entity_id(self) -> str:
        return str(self.session_id)

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(
            element_type=RBACElementType.SESSION,
            element_id=str(self.session_id),
        )


@dataclass
class ModifySessionActionResult(BaseActionResult):
    session_data: SessionData

    @override
    def entity_id(self) -> str | None:
        return str(self.session_data.id)
