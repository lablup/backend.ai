from typing import Any

from ai.backend.manager.actions.registry import ProcessorGroup
from ai.backend.manager.actions.v2.global_scope.processor import (
    GlobalActionProcessor,
    PublicActionProcessor,
)
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
from ai.backend.manager.services.resource_preset.actions.search_presets import (
    SearchResourcePresetsV2Action,
    SearchResourcePresetsV2ActionResult,
)
from ai.backend.manager.services.resource_preset.actions.update_preset import (
    UpdateResourcePresetAction,
    UpdateResourcePresetActionResult,
)
from ai.backend.manager.services.resource_preset.service import ResourcePresetService


class ResourcePresetProcessors:
    create_preset: GlobalActionProcessor[
        CreateResourcePresetAction, CreateResourcePresetActionResult
    ]
    update_preset: GlobalActionProcessor[
        UpdateResourcePresetAction, UpdateResourcePresetActionResult
    ]
    delete_preset: GlobalActionProcessor[
        DeleteResourcePresetAction, DeleteResourcePresetActionResult
    ]
    list_presets: PublicActionProcessor[ListResourcePresetsAction, ListResourcePresetsResult]
    check_presets: PublicActionProcessor[
        CheckResourcePresetsAction, CheckResourcePresetsActionResult
    ]
    search_presets_v2: GlobalActionProcessor[
        SearchResourcePresetsV2Action, SearchResourcePresetsV2ActionResult
    ]

    def __init__(self, group: ProcessorGroup[Any], service: ResourcePresetService) -> None:
        self.create_preset = group.global_scope(CreateResourcePresetAction, service.create_preset)
        self.update_preset = group.global_scope(UpdateResourcePresetAction, service.update_preset)
        self.delete_preset = group.global_scope(DeleteResourcePresetAction, service.delete_preset)
        self.list_presets = group.public(ListResourcePresetsAction, service.list_presets)
        self.check_presets = group.public(CheckResourcePresetsAction, service.check_presets)
        self.search_presets_v2 = group.global_scope(
            SearchResourcePresetsV2Action, service.search_presets_v2
        )
