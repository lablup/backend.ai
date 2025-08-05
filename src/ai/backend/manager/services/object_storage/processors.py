from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.services.object_storage.actions.create import (
    CreateObjectStorageAction,
    CreateObjectStorageActionResult,
)
from ai.backend.manager.services.object_storage.service import ObjectStorageService


class ObjectStorageProcessors(AbstractProcessorPackage):
    create: ActionProcessor[CreateObjectStorageAction, CreateObjectStorageActionResult]

    def __init__(self, service: ObjectStorageService, action_monitors: list[ActionMonitor]) -> None:
        self.create = ActionProcessor(service.create, action_monitors)

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            CreateObjectStorageAction.spec(),
        ]
