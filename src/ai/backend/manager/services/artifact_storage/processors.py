from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.services.artifact_storage.actions.update import (
    UpdateArtifactStorageAction,
    UpdateArtifactStorageActionResult,
)
from ai.backend.manager.services.artifact_storage.service import ArtifactStorageService


class ArtifactStorageProcessors(AbstractProcessorPackage):
    update: ActionProcessor[UpdateArtifactStorageAction, UpdateArtifactStorageActionResult]

    def __init__(
        self, service: ArtifactStorageService, action_monitors: list[ActionMonitor]
    ) -> None:
        self.update = ActionProcessor(service.update, action_monitors)

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            UpdateArtifactStorageAction.spec(),
        ]
