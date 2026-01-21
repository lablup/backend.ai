from dataclasses import dataclass
from typing import Optional, override

from ai.backend.common.types import AccessKey
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.session.types import SessionData
from ai.backend.manager.services.session.base import SessionAction
from ai.backend.manager.services.session.types import CommitStatusInfo


@dataclass
class GetCommitStatusAction(SessionAction):
    session_name: str
    owner_access_key: AccessKey

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "get_commit_status"


@dataclass
class GetCommitStatusActionResult(BaseActionResult):
    commit_info: CommitStatusInfo
    session_data: SessionData

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.session_data.id)
