from __future__ import annotations

from ai.backend.manager.actions.registry import ProcessorGroup
from ai.backend.manager.actions.v2.global_scope.processor import (
    GlobalActionProcessor,
    PublicActionProcessor,
)
from ai.backend.manager.actions.v2.ops.result import (
    BatchOpsResult,
    CreatedEntityOpsResult,
    EntityOpsResult,
)
from ai.backend.manager.data.object_storage.types import ObjectStorageData
from ai.backend.manager.services.object_storage.actions.create import (
    CreateObjectStorageAction,
)
from ai.backend.manager.services.object_storage.actions.get import GetObjectStorageAction
from ai.backend.manager.services.object_storage.actions.get_download_presigned_url import (
    GetDownloadPresignedURLAction,
    GetDownloadPresignedURLActionResult,
)
from ai.backend.manager.services.object_storage.actions.get_upload_presigned_url import (
    GetUploadPresignedURLAction,
    GetUploadPresignedURLActionResult,
)
from ai.backend.manager.services.object_storage.actions.list import ListObjectStorageAction
from ai.backend.manager.services.object_storage.actions.purge import PurgeObjectStorageAction
from ai.backend.manager.services.object_storage.actions.search import (
    SearchObjectStoragesAction,
)
from ai.backend.manager.services.object_storage.actions.update import (
    UpdateObjectStorageAction,
)
from ai.backend.manager.services.object_storage.service import ObjectStorageService


class ObjectStorageProcessors:
    """The registry CRUD runs against ops; only the presigned-URL paths keep a service."""

    create: GlobalActionProcessor[
        CreateObjectStorageAction, CreatedEntityOpsResult[ObjectStorageData]
    ]
    update: GlobalActionProcessor[UpdateObjectStorageAction, EntityOpsResult[ObjectStorageData]]
    purge: GlobalActionProcessor[PurgeObjectStorageAction, EntityOpsResult[ObjectStorageData]]
    get: PublicActionProcessor[GetObjectStorageAction, EntityOpsResult[ObjectStorageData]]
    list_storages: PublicActionProcessor[ListObjectStorageAction, BatchOpsResult[ObjectStorageData]]
    search_object_storages: PublicActionProcessor[
        SearchObjectStoragesAction, BatchOpsResult[ObjectStorageData]
    ]
    get_presigned_download_url: GlobalActionProcessor[
        GetDownloadPresignedURLAction, GetDownloadPresignedURLActionResult
    ]
    get_presigned_upload_url: GlobalActionProcessor[
        GetUploadPresignedURLAction, GetUploadPresignedURLActionResult
    ]

    def __init__(
        self,
        service: ObjectStorageService,
        group: ProcessorGroup[ObjectStorageData],
    ) -> None:
        self.create = group.global_create_ops(CreateObjectStorageAction)
        self.update = group.global_update_ops(UpdateObjectStorageAction)
        self.purge = group.global_purge_ops(PurgeObjectStorageAction)
        self.get = group.public_get_ops(GetObjectStorageAction)
        self.list_storages = group.public_search_ops(ListObjectStorageAction)
        self.search_object_storages = group.public_search_ops(SearchObjectStoragesAction)
        self.get_presigned_download_url = group.global_scope(
            GetDownloadPresignedURLAction, service.get_presigned_download_url
        )
        self.get_presigned_upload_url = group.global_scope(
            GetUploadPresignedURLAction, service.get_presigned_upload_url
        )
