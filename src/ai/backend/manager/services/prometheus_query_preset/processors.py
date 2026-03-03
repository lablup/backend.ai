from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.services.prometheus_query_preset.actions.create_preset import (
    CreatePresetAction,
    CreatePresetActionResult,
)
from ai.backend.manager.services.prometheus_query_preset.actions.delete_preset import (
    DeletePresetAction,
    DeletePresetActionResult,
)
from ai.backend.manager.services.prometheus_query_preset.actions.execute_preset import (
    ExecutePresetAction,
    ExecutePresetActionResult,
)
from ai.backend.manager.services.prometheus_query_preset.actions.get_preset import (
    GetPresetAction,
    GetPresetActionResult,
)
from ai.backend.manager.services.prometheus_query_preset.actions.list_presets import (
    ListPresetsAction,
    ListPresetsActionResult,
)
from ai.backend.manager.services.prometheus_query_preset.actions.modify_preset import (
    ModifyPresetAction,
    ModifyPresetActionResult,
)
from ai.backend.manager.services.prometheus_query_preset.service import (
    PrometheusQueryPresetService,
)


class PrometheusQueryPresetProcessors(AbstractProcessorPackage):
    create_preset: ActionProcessor[CreatePresetAction, CreatePresetActionResult]
    get_preset: ActionProcessor[GetPresetAction, GetPresetActionResult]
    list_presets: ActionProcessor[ListPresetsAction, ListPresetsActionResult]
    modify_preset: ActionProcessor[ModifyPresetAction, ModifyPresetActionResult]
    delete_preset: ActionProcessor[DeletePresetAction, DeletePresetActionResult]
    execute_preset: ActionProcessor[ExecutePresetAction, ExecutePresetActionResult]

    def __init__(
        self, service: PrometheusQueryPresetService, action_monitors: list[ActionMonitor]
    ) -> None:
        self.create_preset = ActionProcessor(service.create_preset, action_monitors)
        self.get_preset = ActionProcessor(service.get_preset, action_monitors)
        self.list_presets = ActionProcessor(service.list_presets, action_monitors)
        self.modify_preset = ActionProcessor(service.modify_preset, action_monitors)
        self.delete_preset = ActionProcessor(service.delete_preset, action_monitors)
        self.execute_preset = ActionProcessor(service.execute_preset, action_monitors)

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            CreatePresetAction.spec(),
            GetPresetAction.spec(),
            ListPresetsAction.spec(),
            ModifyPresetAction.spec(),
            DeletePresetAction.spec(),
            ExecutePresetAction.spec(),
        ]
