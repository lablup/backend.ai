import uuid
from dataclasses import dataclass
from typing import Any, Optional, override

from ai.backend.common.types import AccessKey
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.session.base import SessionAction


@dataclass
class GetStatusHistoryAction(SessionAction):
    session_name: str
    owner_access_key: AccessKey

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "get_status_history"


@dataclass
class GetStatusHistoryActionResult(BaseActionResult):
    status_history: dict[str, Any]
    session_id: uuid.UUID

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.session_id)
