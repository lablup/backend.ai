from dataclasses import dataclass
from typing import Any, Optional, override

from ai.backend.common.types import AccessKey
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.services.session.base import SessionAction


@dataclass
class StartServiceAction(SessionAction):
    session_name: str
    access_key: AccessKey
    service: str
    login_session_token: Any
    port: Optional[int]
    arguments: Optional[str]  # json_string
    envs: Optional[str]  # json_string

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def operation_type(self):
        return "start_service"


@dataclass
class StartServiceActionResult(BaseActionResult):
    # TODO: Add proper type
    result: Any
    session_row: SessionRow
    token: str
    wsproxy_addr: str

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.session_row.id)
