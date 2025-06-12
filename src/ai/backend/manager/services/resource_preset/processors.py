from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.services.resource_preset.actions.check_presets import (
    CheckResourcePresetsAction,
    CheckResourcePresetsActionResult,
)
from ai.backend.manager.services.resource_preset.actions.create_preset import (
    CreateResourcePresetAction,
    CreateResourcePresetActionResult,
)
from ai.backend.manager.services.resource_preset.actions.delete_preset import (
    DeleteResourcePresetAction,
    DeleteResourcePresetActionResult,
)
from ai.backend.manager.services.resource_preset.actions.list_presets import (
    ListResourcePresetsAction,
    ListResourcePresetsResult,
)
from ai.backend.manager.services.resource_preset.actions.modify_preset import (
    ModifyResourcePresetAction,
    ModifyResourcePresetActionResult,
)
from ai.backend.manager.services.resource_preset.service import ResourcePresetService


class ResourcePresetProcessors(AbstractProcessorPackage):
    create_preset: ActionProcessor[CreateResourcePresetAction, CreateResourcePresetActionResult]
    modify_preset: ActionProcessor[ModifyResourcePresetAction, ModifyResourcePresetActionResult]
    delete_preset: ActionProcessor[DeleteResourcePresetAction, DeleteResourcePresetActionResult]
    list_presets: ActionProcessor[ListResourcePresetsAction, ListResourcePresetsResult]
    check_presets: ActionProcessor[CheckResourcePresetsAction, CheckResourcePresetsActionResult]

    def __init__(
        self, service: ResourcePresetService, action_monitors: list[ActionMonitor]
    ) -> None:
        self.create_preset = ActionProcessor(service.create_preset, action_monitors)
        self.modify_preset = ActionProcessor(service.modify_preset, action_monitors)
        self.delete_preset = ActionProcessor(service.delete_preset, action_monitors)
        self.list_presets = ActionProcessor(service.list_presets, action_monitors)
        self.check_presets = ActionProcessor(service.check_presets, action_monitors)

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            CreateResourcePresetAction.spec(),
            ModifyResourcePresetAction.spec(),
            DeleteResourcePresetAction.spec(),
            ListResourcePresetsAction.spec(),
            CheckResourcePresetsAction.spec(),
        ]
