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
from ai.backend.manager.services.object_storage.actions.get import (
    GetObjectStorageAction,
    GetObjectStorageActionResult,
)
from ai.backend.manager.services.object_storage.actions.get_download_presigned_url import (
    GetDownloadPresignedURLAction,
    GetDownloadPresignedURLActionResult,
)
from ai.backend.manager.services.object_storage.actions.get_upload_presigned_url import (
    GetUploadPresignedURLAction,
    GetUploadPresignedURLActionResult,
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
    get: ActionProcessor[GetObjectStorageAction, GetObjectStorageActionResult]
    list_storages: ActionProcessor[ListObjectStorageAction, ListObjectStorageActionResult]
    get_presigned_download_url: ActionProcessor[
        GetDownloadPresignedURLAction, GetDownloadPresignedURLActionResult
    ]
    get_presigned_upload_url: ActionProcessor[
        GetUploadPresignedURLAction, GetUploadPresignedURLActionResult
    ]

    def __init__(self, service: ObjectStorageService, action_monitors: list[ActionMonitor]) -> None:
        self.create = ActionProcessor(service.create, action_monitors)
        self.update = ActionProcessor(service.update, action_monitors)
        self.delete = ActionProcessor(service.delete, action_monitors)
        self.get = ActionProcessor(service.get, action_monitors)
        self.list_storages = ActionProcessor(service.list, action_monitors)
        self.get_presigned_download_url = ActionProcessor(
            service.get_presigned_download_url, action_monitors
        )
        self.get_presigned_upload_url = ActionProcessor(
            service.get_presigned_upload_url, action_monitors
        )

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            CreateObjectStorageAction.spec(),
            UpdateObjectStorageAction.spec(),
            DeleteObjectStorageAction.spec(),
            GetObjectStorageAction.spec(),
            ListObjectStorageAction.spec(),
            GetDownloadPresignedURLAction.spec(),
            GetUploadPresignedURLAction.spec(),
        ]
