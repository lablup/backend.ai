from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.services.resource_preset.actions.check_presets import (
    CheckResourcePresetsAction,
    CheckResourcePresetsActionResult,
)
from ai.backend.manager.services.resource_preset.actions.create_preset import (
    CreateResourcePresetAction,
    CreateResourcePresetActionResult,
)
from ai.backend.manager.services.resource_preset.actions.list_presets import (
    ListResourcePresetsAction,
    ListResourcePresetsResult,
)
from ai.backend.manager.services.resource_preset.service import ResourcePresetService


class ResourcePresetProcessors:
    create_preset: ActionProcessor[CreateResourcePresetAction, CreateResourcePresetActionResult]
    list_presets: ActionProcessor[ListResourcePresetsAction, ListResourcePresetsResult]
    check_presets: ActionProcessor[CheckResourcePresetsAction, CheckResourcePresetsActionResult]

    def __init__(self, service: ResourcePresetService) -> None:
        self.create_preset = ActionProcessor(service.create_preset)
        self.list_presets = ActionProcessor(service.list_presets)
        self.check_presets = ActionProcessor(service.check_presets)
