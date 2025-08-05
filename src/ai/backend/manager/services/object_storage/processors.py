from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.services.object_storage.actions.create import (
    CreateObjectStorageAction,
    CreateObjectStorageActionResult,
)
from ai.backend.manager.services.object_storage.actions.delete import (
    DeleteObjectStorageAction,
    DeleteObjectStorageActionResult,
)
from ai.backend.manager.services.object_storage.actions.list import (
    ListObjectStorageAction,
    ListObjectStorageActionResult,
)
from ai.backend.manager.services.object_storage.actions.update import (
    UpdateObjectStorageAction,
    UpdateObjectStorageActionResult,
)
from ai.backend.manager.services.object_storage.service import ObjectStorageService


class ObjectStorageProcessors(AbstractProcessorPackage):
    create: ActionProcessor[CreateObjectStorageAction, CreateObjectStorageActionResult]
    update: ActionProcessor[UpdateObjectStorageAction, UpdateObjectStorageActionResult]
    delete: ActionProcessor[DeleteObjectStorageAction, DeleteObjectStorageActionResult]
    list_: ActionProcessor[ListObjectStorageAction, ListObjectStorageActionResult]

    def __init__(self, service: ObjectStorageService, action_monitors: list[ActionMonitor]) -> None:
        self.create = ActionProcessor(service.create, action_monitors)
        self.update = ActionProcessor(service.update, action_monitors)
        self.delete = ActionProcessor(service.delete, action_monitors)
        self.list_ = ActionProcessor(service.list, action_monitors)

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            CreateObjectStorageAction.spec(),
            UpdateObjectStorageAction.spec(),
            DeleteObjectStorageAction.spec(),
            ListObjectStorageAction.spec(),
        ]
