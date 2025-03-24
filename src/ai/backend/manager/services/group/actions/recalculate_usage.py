from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.group.base import GroupAction


@dataclass
class RecalculateUsageAction(GroupAction):
    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def operation_type(self):
        return "recalculate_usage"


@dataclass
class RecalculateUsageActionResult(BaseActionResult):
    @override
    def entity_id(self) -> Optional[str]:
        return None
