from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.types import AccessKey
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.session.types import SessionData
from ai.backend.manager.services.session.base import SessionSingleEntityAction


@dataclass
class ExecuteSessionActionParams:
    mode: str | None
    # TODO: Add proper type
    options: Any | None
    code: str | None
    run_id: str | None


@dataclass
class ExecuteSessionAction(SessionSingleEntityAction):
    """Execute code in a specific session.

    RBAC validation checks if the user has UPDATE permission for this session.
    session_id must be resolved from session_name before RBAC validation.
    """

    session_name: str
    api_version: tuple[Any, ...]
    owner_access_key: AccessKey
    params: ExecuteSessionActionParams

    @override
    def entity_id(self) -> str | None:
        return self.session_id if self.session_id else None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class ExecuteSessionActionResult(BaseActionResult):
    # TODO: Add proper type
    result: Any
    session_data: SessionData

    @override
    def entity_id(self) -> str | None:
        return str(self.session_data.id)
