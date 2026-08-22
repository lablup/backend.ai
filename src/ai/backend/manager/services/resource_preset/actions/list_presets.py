from dataclasses import dataclass
from typing import Any, override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.resource_preset.actions.base import ResourcePresetAction


@dataclass
class ListResourcePresetsAction(ResourcePresetAction):
    access_key: str
    resource_group: str | None

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_list_resource_presets"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass
class ListResourcePresetsResult:
    # TODO: Add preset type
    presets: list[Any]
