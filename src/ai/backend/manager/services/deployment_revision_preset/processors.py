from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.actions.validators import ActionValidators
from ai.backend.manager.services.deployment_revision_preset.actions.create import (
    CreateDeploymentRevisionPresetAction,
    CreateDeploymentRevisionPresetActionResult,
)
from ai.backend.manager.services.deployment_revision_preset.actions.delete import (
    DeleteDeploymentRevisionPresetAction,
    DeleteDeploymentRevisionPresetActionResult,
)
from ai.backend.manager.services.deployment_revision_preset.actions.search import (
    SearchDeploymentRevisionPresetsAction,
    SearchDeploymentRevisionPresetsActionResult,
)
from ai.backend.manager.services.deployment_revision_preset.actions.search_resource_slots import (
    SearchPresetResourceSlotsAction,
    SearchPresetResourceSlotsActionResult,
)
from ai.backend.manager.services.deployment_revision_preset.actions.update import (
    UpdateDeploymentRevisionPresetAction,
    UpdateDeploymentRevisionPresetActionResult,
)
from ai.backend.manager.services.deployment_revision_preset.service import (
    DeploymentRevisionPresetService,
)


class DeploymentRevisionPresetProcessors(AbstractProcessorPackage):
    create: ActionProcessor[
        CreateDeploymentRevisionPresetAction, CreateDeploymentRevisionPresetActionResult
    ]
    update: ActionProcessor[
        UpdateDeploymentRevisionPresetAction, UpdateDeploymentRevisionPresetActionResult
    ]
    delete: ActionProcessor[
        DeleteDeploymentRevisionPresetAction, DeleteDeploymentRevisionPresetActionResult
    ]
    search: ActionProcessor[
        SearchDeploymentRevisionPresetsAction, SearchDeploymentRevisionPresetsActionResult
    ]
    search_resource_slots: ActionProcessor[
        SearchPresetResourceSlotsAction, SearchPresetResourceSlotsActionResult
    ]

    def __init__(
        self,
        service: DeploymentRevisionPresetService,
        action_monitors: list[ActionMonitor],
        validators: ActionValidators,
    ) -> None:
        self.create = ActionProcessor(service.create, action_monitors)
        self.update = ActionProcessor(service.update, action_monitors)
        self.delete = ActionProcessor(service.delete, action_monitors)
        self.search = ActionProcessor(service.search, action_monitors)
        self.search_resource_slots = ActionProcessor(service.search_resource_slots, action_monitors)

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            CreateDeploymentRevisionPresetAction.spec(),
            UpdateDeploymentRevisionPresetAction.spec(),
            DeleteDeploymentRevisionPresetAction.spec(),
            SearchDeploymentRevisionPresetsAction.spec(),
            SearchPresetResourceSlotsAction.spec(),
        ]
