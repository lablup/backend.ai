from dataclasses import dataclass
from typing import Any, override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.session.types import SessionData
from ai.backend.manager.services.session.base import (
    SessionAction,
)


@dataclass
class StartServiceAction(SessionAction):
    service: str
    login_session_token: Any
    port: int | None
    arguments: str | None  # json_string
    envs: str | None  # json_string

    @override
    @classmethod
    def action_name(cls) -> str:
        return "start_service"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


@dataclass
class StartServiceActionResult:
    # TODO: Add proper type
    result: Any
    session_data: SessionData
    token: str
    wsproxy_addr: str
