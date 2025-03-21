from dataclasses import dataclass
from typing import Any, Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.resource.base import ResourceAction


@dataclass
class RecalculateUsageAction(ResourceAction):
    @override
    def entity_id(self) -> str:
        # TODO: ?
        return ""

    @override
    def operation_type(self):
        return "recalculate_usage"


@dataclass
class RecalculateUsageActionResult(BaseActionResult):
    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def status(self) -> str:
        return "success"

    @override
    def description(self) -> Optional[str]:
        return "Resource presets listed successfully."

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, type(self)):
            return False
        return True
        # # TODO: 여기선 id로 비교못할 듯.
        # return self.image_alias.alias == other.image_alias.alias
