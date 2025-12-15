import uuid
from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.session.types import SessionData
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.services.session.base import SessionAction


@dataclass
class ModifySessionAction(SessionAction):
    session_id: uuid.UUID
    updater: Updater[SessionRow]

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.session_id)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "modify"


@dataclass
class ModifySessionActionResult(BaseActionResult):
    session_data: SessionData

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.session_data.id)
