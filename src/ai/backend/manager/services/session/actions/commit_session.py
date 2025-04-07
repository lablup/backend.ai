from dataclasses import dataclass
from typing import Any, Mapping, Optional, override

from ai.backend.common.types import AccessKey
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.services.session.base import SessionAction


@dataclass
class CommitSessionAction(SessionAction):
    session_name: str
    owner_access_key: AccessKey
    filename: Optional[str]

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def operation_type(self):
        return "commit"


@dataclass
class CommitSessionActionResult(BaseActionResult):
    # TODO: Add SessionData type
    session_row: SessionRow

    # TODO: Add proper type
    commit_result: Mapping[str, Any]

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.session_row.id)
