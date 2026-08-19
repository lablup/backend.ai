from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.types import AccessKey
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.session.types import SessionData
from ai.backend.manager.services.session.actions.app_service_base import SessionAppServiceAction


@dataclass
class ShutdownServiceAction(SessionAppServiceAction):
    session_name: str
    owner_access_key: AccessKey
    service_name: str

    @override
    @classmethod
    def action_name(cls) -> str:
        return "shutdown_service"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE


@dataclass
class ShutdownServiceActionResult:
    # TODO: Add proper type
    result: Any
    session_data: SessionData
