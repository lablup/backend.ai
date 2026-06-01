from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.common.identifier.session import SessionID
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.data.session.types import SessionData
from ai.backend.manager.services.session.base import (
    SessionSingleEntityAction,
    SessionSingleEntityActionResult,
)


@dataclass
class StartServiceAction(SessionSingleEntityAction):
    session_id: SessionID
    service: str
    login_session_token: Any
    port: int | None
    arguments: str | None  # json_string
    envs: str | None  # json_string

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE

    @override
    def target_entity_id(self) -> str:
        return str(self.session_id)

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.SESSION, str(self.session_id))


@dataclass
class StartServiceActionResult(SessionSingleEntityActionResult):
    # TODO: Add proper type
    result: Any
    session_data: SessionData
    token: str
    wsproxy_addr: str

    @override
    def target_entity_id(self) -> str:
        return str(self.session_data.id)
