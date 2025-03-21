from dataclasses import dataclass
from typing import Any, Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.resource.base import ResourceAction


@dataclass
class ListResourcePresetsAction(ResourceAction):
    access_key: str
    scaling_group: Optional[str] = None

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def operation_type(self):
        return "list_resource_presets"


@dataclass
class ListResourcePresetsResult(BaseActionResult):
    # TODO: Add preset type
    presets: list[Any]

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
