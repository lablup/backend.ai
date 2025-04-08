from dataclasses import dataclass
from typing import Any, Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.resource_preset.base import ResourcePresetAction


@dataclass
class ListResourcePresetsAction(ResourcePresetAction):
    access_key: str
    scaling_group: Optional[str]

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
        # TODO: Should return preset row ids after changing to batching.
        return None
