from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.session.types import SessionData
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.services.session.base import (
    SessionAction,
)


@dataclass
class UpdateSessionAction(SessionAction):
    updater: Updater[SessionRow]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "update_session"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class UpdateSessionActionResult:
    session_data: SessionData
