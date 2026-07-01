from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.common.types import SessionId
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.data.session.types import SessionData
from ai.backend.manager.services.session.base import (
    SessionSingleEntityAction,
    SessionSingleEntityActionResult,
)


@dataclass
class GetSessionAction(SessionSingleEntityAction):
    session_id: SessionId

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    def target_entity_id(self) -> str:
        return str(self.session_id)

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.SESSION, str(self.session_id))


@dataclass
class GetSessionActionResult(SessionSingleEntityActionResult):
    session_data: SessionData

    @override
    def target_entity_id(self) -> str:
        return str(self.session_data.id)
