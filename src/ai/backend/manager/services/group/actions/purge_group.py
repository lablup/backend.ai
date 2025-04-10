import uuid
from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.group.actions.base import GroupAction
from ai.backend.manager.services.group.types import GroupData


@dataclass
class PurgeGroupAction(GroupAction):
    group_id: uuid.UUID

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def operation_type(self) -> str:
        return "purge"


@dataclass
class PurgeGroupActionResult(BaseActionResult):
    data: Optional[GroupData]
    success: bool

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.data.id) if self.data is not None else None
