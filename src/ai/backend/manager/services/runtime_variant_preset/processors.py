from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.actions.validators import ActionValidators
from ai.backend.manager.services.runtime_variant_preset.actions.create import (
    CreateRuntimeVariantPresetAction,
    CreateRuntimeVariantPresetActionResult,
)
from ai.backend.manager.services.runtime_variant_preset.actions.delete import (
    DeleteRuntimeVariantPresetAction,
    DeleteRuntimeVariantPresetActionResult,
)
from ai.backend.manager.services.runtime_variant_preset.actions.search import (
    SearchRuntimeVariantPresetsAction,
    SearchRuntimeVariantPresetsActionResult,
)
from ai.backend.manager.services.runtime_variant_preset.actions.update import (
    UpdateRuntimeVariantPresetAction,
    UpdateRuntimeVariantPresetActionResult,
)
from ai.backend.manager.services.runtime_variant_preset.service import RuntimeVariantPresetService


class RuntimeVariantPresetProcessors(AbstractProcessorPackage):
    create: ActionProcessor[
        CreateRuntimeVariantPresetAction, CreateRuntimeVariantPresetActionResult
    ]
    update: ActionProcessor[
        UpdateRuntimeVariantPresetAction, UpdateRuntimeVariantPresetActionResult
    ]
    delete: ActionProcessor[
        DeleteRuntimeVariantPresetAction, DeleteRuntimeVariantPresetActionResult
    ]
    search: ActionProcessor[
        SearchRuntimeVariantPresetsAction, SearchRuntimeVariantPresetsActionResult
    ]

    def __init__(
        self,
        service: RuntimeVariantPresetService,
        action_monitors: list[ActionMonitor],
        validators: ActionValidators,
    ) -> None:
        self.create = ActionProcessor(service.create, action_monitors)
        self.update = ActionProcessor(service.update, action_monitors)
        self.delete = ActionProcessor(service.delete, action_monitors)
        self.search = ActionProcessor(service.search, action_monitors)

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            CreateRuntimeVariantPresetAction.spec(),
            UpdateRuntimeVariantPresetAction.spec(),
            DeleteRuntimeVariantPresetAction.spec(),
            SearchRuntimeVariantPresetsAction.spec(),
        ]
