from dataclasses import dataclass
from typing import Any, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.resource_preset.actions.base import ResourcePresetAction


@dataclass
class ListResourcePresetsAction(ResourcePresetAction):
    access_key: str
    scaling_group: str | None

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "list_multi"


@dataclass
class ListResourcePresetsResult(BaseActionResult):
    # TODO: Add preset type
    presets: list[Any]

    @override
    def entity_id(self) -> str | None:
        # TODO: Should return preset row ids after changing to batching.
        return None
