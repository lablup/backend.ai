import uuid
from dataclasses import dataclass
from typing import Any, Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.groups.base import GroupAction


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
    data: Optional[Any] = None

    @override
    def entity_id(self) -> Optional[str]:
        return None
