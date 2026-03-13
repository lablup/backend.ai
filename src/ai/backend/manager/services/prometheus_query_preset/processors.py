from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.actions.validators import ActionValidators
from ai.backend.manager.services.prometheus_query_preset.actions import (
    CreatePresetAction,
    CreatePresetActionResult,
    DeletePresetAction,
    DeletePresetActionResult,
    ExecutePresetAction,
    ExecutePresetActionResult,
    GetPresetAction,
    GetPresetActionResult,
    ModifyPresetAction,
    ModifyPresetActionResult,
    SearchPresetsAction,
    SearchPresetsActionResult,
)
from ai.backend.manager.services.prometheus_query_preset.service import (
    PrometheusQueryPresetService,
)


class PrometheusQueryPresetProcessors(AbstractProcessorPackage):
    create_preset: ActionProcessor[CreatePresetAction, CreatePresetActionResult]
    get_preset: ActionProcessor[GetPresetAction, GetPresetActionResult]
    search_presets: ActionProcessor[SearchPresetsAction, SearchPresetsActionResult]
    modify_preset: ActionProcessor[ModifyPresetAction, ModifyPresetActionResult]
    delete_preset: ActionProcessor[DeletePresetAction, DeletePresetActionResult]
    execute_preset: ActionProcessor[ExecutePresetAction, ExecutePresetActionResult]

    def __init__(
        self,
        service: PrometheusQueryPresetService,
        action_monitors: list[ActionMonitor],
        validators: ActionValidators,
    ) -> None:
        self.create_preset = ActionProcessor(service.create_preset, action_monitors)
        self.get_preset = ActionProcessor(service.get_preset, action_monitors)
        self.search_presets = ActionProcessor(service.search_presets, action_monitors)
        self.modify_preset = ActionProcessor(service.modify_preset, action_monitors)
        self.delete_preset = ActionProcessor(service.delete_preset, action_monitors)
        self.execute_preset = ActionProcessor(service.execute_preset, action_monitors)

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            CreatePresetAction.spec(),
            GetPresetAction.spec(),
            SearchPresetsAction.spec(),
            ModifyPresetAction.spec(),
            DeletePresetAction.spec(),
            ExecutePresetAction.spec(),
        ]
