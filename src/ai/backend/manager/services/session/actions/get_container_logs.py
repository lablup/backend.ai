from dataclasses import dataclass
from typing import Optional, override

from ai.backend.common.types import AccessKey, KernelId
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.session.types import SessionData
from ai.backend.manager.services.session.base import SessionAction


@dataclass
class GetContainerLogsAction(SessionAction):
    session_name: str
    owner_access_key: AccessKey
    kernel_id: Optional[KernelId]

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "get_container_logs"


@dataclass
class GetContainerLogsActionResult(BaseActionResult):
    result: dict[str, dict[str, str]]
    session_data: SessionData

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.session_data.id)
