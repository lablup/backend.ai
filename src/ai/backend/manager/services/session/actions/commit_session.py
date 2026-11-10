from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.types import AccessKey
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.session.types import SessionData
from ai.backend.manager.services.session.actions.commit_base import SessionCommitAction


@dataclass
class CommitSessionAction(SessionCommitAction):
    session_name: str
    owner_access_key: AccessKey
    filename: str | None

    @override
    @classmethod
    def action_name(cls) -> str:
        return "commit_session"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


@dataclass
class CommitSessionActionResult:
    session_data: SessionData

    # TODO: Add proper type
    commit_result: Mapping[str, Any]
