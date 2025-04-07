from dataclasses import dataclass
from typing import Any, Optional, override

from ai.backend.common.types import AccessKey, KernelId
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.models.session import SessionRow
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
    def operation_type(self):
        return "get_container_logs"


@dataclass
class GetContainerLogsActionResult(BaseActionResult):
    # TODO: Add proper type
    result: Any
    session_row: SessionRow

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.session_row.id)
