from dataclasses import dataclass
from typing import Any, Mapping, Optional, override

from ai.backend.common.types import AccessKey
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.services.session.base import SessionAction


# TODO: Rename this?
@dataclass
class CompleteAction(SessionAction):
    session_name: str
    owner_access_key: AccessKey
    code: str
    # TODO: Add type
    options: Optional[Mapping[str, Any]]

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "complete"


@dataclass
class CompleteActionResult(BaseActionResult):
    # TODO: Add SessionData type
    session_row: SessionRow

    # TODO: Add proper type
    result: dict[str, Any]

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.session_row.id)
