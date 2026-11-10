from dataclasses import dataclass
from typing import override

from ai.backend.common.types import AccessKey
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.session.types import SessionData
from ai.backend.manager.services.session.actions.commit_base import SessionCommitAction
from ai.backend.manager.services.session.types import CommitStatusInfo


@dataclass
class GetCommitStatusAction(SessionCommitAction):
    session_name: str
    owner_access_key: AccessKey

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_commit_status"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class GetCommitStatusActionResult:
    commit_info: CommitStatusInfo
    session_data: SessionData
