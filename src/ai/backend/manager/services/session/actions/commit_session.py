from dataclasses import dataclass
from typing import Any, Mapping, Optional, override

from ai.backend.common.types import AccessKey
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.session.types import SessionData
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
    @classmethod
    def operation_type(cls) -> str:
        return "commit"


@dataclass
class CommitSessionActionResult(BaseActionResult):
    session_data: SessionData

    # TODO: Add proper type
    commit_result: Mapping[str, Any]

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.session_data.id)
