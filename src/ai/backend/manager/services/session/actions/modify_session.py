import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.session.types import SessionData
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.services.session.base import SessionSingleEntityAction


@dataclass
class ModifySessionAction(SessionSingleEntityAction):
    """Modify a specific session.

    RBAC validation checks if the user has UPDATE permission for this session.
    session_id (str) is automatically set from the session_uuid (UUID) field.
    """

    session_uuid: uuid.UUID  # Renamed to avoid conflict with base class session_id
    updater: Updater[SessionRow]

    def __post_init__(self) -> None:
        # Set session_id (str) for RBAC validation from session_uuid (UUID)
        object.__setattr__(self, "session_id", str(self.session_uuid))

    @override
    def entity_id(self) -> str | None:
        return str(self.session_uuid)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class ModifySessionActionResult(BaseActionResult):
    session_data: SessionData

    @override
    def entity_id(self) -> str | None:
        return str(self.session_data.id)
