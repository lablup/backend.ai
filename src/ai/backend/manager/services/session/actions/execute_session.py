import uuid
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.common.types import AccessKey
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.data.session.types import SessionData
from ai.backend.manager.services.session.base import (
    SessionSingleEntityAction,
    SessionSingleEntityActionResult,
)


@dataclass
class ExecuteSessionActionParams:
    mode: str | None
    # TODO: Add proper type
    options: Any | None
    code: str | None
    run_id: str | None


@dataclass
class ExecuteSessionAction(SessionSingleEntityAction):
    session_id: uuid.UUID
    api_version: tuple[Any, ...]
    owner_access_key: AccessKey
    params: ExecuteSessionActionParams

    @override
    def target_entity_id(self) -> str:
        return str(self.session_id)

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.SESSION, str(self.session_id))

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class ExecuteSessionActionResult(SessionSingleEntityActionResult):
    # TODO: Add proper type
    result: Any
    session_data: SessionData

    @override
    def target_entity_id(self) -> str:
        return str(self.session_data.id)
