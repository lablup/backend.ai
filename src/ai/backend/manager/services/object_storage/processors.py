from __future__ import annotations

from ai.backend.manager.actions.registry import ProcessorGroup
from ai.backend.manager.actions.v2.global_scope.processor import GlobalActionProcessor
from ai.backend.manager.actions.v2.ops.result import (
    BatchOpsResult,
    CreatedEntityOpsResult,
    EntityOpsResult,
)
from ai.backend.manager.actions.v2.single_entity.processor import (
    SingleEntityActionProcessor,
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

    global_create: GlobalActionProcessor[
        CreateObjectStorageAction, CreatedEntityOpsResult[ObjectStorageData]
    ]
    update: SingleEntityActionProcessor[
        UpdateObjectStorageAction, EntityOpsResult[ObjectStorageData]
    ]
    purge: SingleEntityActionProcessor[PurgeObjectStorageAction, EntityOpsResult[ObjectStorageData]]
    get: SingleEntityActionProcessor[GetObjectStorageAction, EntityOpsResult[ObjectStorageData]]
    global_list_storages: GlobalActionProcessor[
        ListObjectStorageAction, BatchOpsResult[ObjectStorageData]
    ]
    global_search_object_storages: GlobalActionProcessor[
        SearchObjectStoragesAction, BatchOpsResult[ObjectStorageData]
    ]
    get_presigned_download_url: SingleEntityActionProcessor[
        GetDownloadPresignedURLAction, GetDownloadPresignedURLActionResult
    ]
    get_presigned_upload_url: SingleEntityActionProcessor[
        GetUploadPresignedURLAction, GetUploadPresignedURLActionResult
    ]

    def __init__(
        self,
        group: ProcessorGroup[ObjectStorageData],
        service: ObjectStorageService,
    ) -> None:
        self.global_create = group.global_create_ops(CreateObjectStorageAction)
        self.update = group.single_update_ops(UpdateObjectStorageAction)
        self.purge = group.entity_purge_ops(PurgeObjectStorageAction)
        self.get = group.single_get_ops(GetObjectStorageAction)
        self.global_list_storages = group.global_search_ops(ListObjectStorageAction)
        self.global_search_object_storages = group.global_search_ops(SearchObjectStoragesAction)
        self.get_presigned_download_url = group.single_entity(
            GetDownloadPresignedURLAction, service.get_presigned_download_url
        )
        self.get_presigned_upload_url = group.single_entity(
            GetUploadPresignedURLAction, service.get_presigned_upload_url
        )
