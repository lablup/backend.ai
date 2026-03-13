"""Object storage handler class using constructor dependency injection."""

from __future__ import annotations

import json
import logging
import uuid
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from ai.backend.common.api_handlers import APIResponse, BodyParam, PathParam
from ai.backend.common.dto.manager.request import (
    GetPresignedDownloadURLReq,
    GetPresignedUploadURLReq,
    ObjectStoragePathParam,
)
from ai.backend.common.dto.manager.response import (
    GetPresignedDownloadURLResponse,
    GetPresignedUploadURLResponse,
    ObjectStorageAllBucketsResponse,
    ObjectStorageBucketsResponse,
    ObjectStorageListResponse,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.services.object_storage.actions.get_download_presigned_url import (
    GetDownloadPresignedURLAction,
)
from ai.backend.manager.services.object_storage.actions.get_upload_presigned_url import (
    GetUploadPresignedURLAction,
)
from ai.backend.manager.services.object_storage.actions.list import (
    ListObjectStorageAction,
)
from ai.backend.manager.services.storage_namespace.actions.get_all import GetAllNamespacesAction
from ai.backend.manager.services.storage_namespace.actions.get_multi import GetNamespacesAction

if TYPE_CHECKING:
    from ai.backend.manager.services.object_storage.processors import ObjectStorageProcessors
    from ai.backend.manager.services.storage_namespace.processors import StorageNamespaceProcessors

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ObjectStorageHandler:
    """Object storage API handler with constructor-injected dependencies."""

    def __init__(
        self,
        *,
        object_storage: ObjectStorageProcessors,
        storage_namespace: StorageNamespaceProcessors,
    ) -> None:
        self._object_storage = object_storage
        self._storage_namespace = storage_namespace

    async def get_presigned_download_url(
        self,
        body: BodyParam[GetPresignedDownloadURLReq],
    ) -> APIResponse:
        """Generate a presigned URL for safely downloading artifact files."""
        action_result = await self._object_storage.get_presigned_download_url.wait_for_complete(
            GetDownloadPresignedURLAction(
                artifact_revision_id=body.parsed.artifact_revision_id,
                key=body.parsed.key,
                expiration=body.parsed.expiration,
            )
        )

        resp = GetPresignedDownloadURLResponse(presigned_url=action_result.presigned_url)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    async def get_presigned_upload_url(
        self,
        body: BodyParam[GetPresignedUploadURLReq],
    ) -> APIResponse:
        """Generate a presigned URL for uploading artifact files."""
        action_result = await self._object_storage.get_presigned_upload_url.wait_for_complete(
            GetUploadPresignedURLAction(
                artifact_revision_id=body.parsed.artifact_revision_id,
                key=body.parsed.key,
            )
        )

        resp = GetPresignedUploadURLResponse(
            presigned_url=action_result.presigned_url,
            fields=json.dumps(action_result.fields),
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    async def get_all_buckets(
        self,
    ) -> APIResponse:
        """Retrieve all storage namespaces (buckets) across all storage systems.

        Note: This API is deprecated. Use /storage-namespaces instead.
        """
        action_result = await self._storage_namespace.get_all_namespaces.wait_for_complete(
            GetAllNamespacesAction()
        )

        resp = ObjectStorageAllBucketsResponse(buckets_by_storage=action_result.result)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    async def get_buckets(
        self,
        path: PathParam[ObjectStoragePathParam],
    ) -> APIResponse:
        """Retrieve storage namespaces (buckets) for a specific storage system.

        Note: This API is deprecated. Use /storage-namespaces instead.
        """
        storage_id: uuid.UUID = path.parsed.storage_id

        action_result = await self._storage_namespace.get_namespaces.wait_for_complete(
            GetNamespacesAction(storage_id=storage_id)
        )

        bucket_names = [namespace_data.namespace for namespace_data in action_result.result]
        resp = ObjectStorageBucketsResponse(buckets=bucket_names)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    async def list_object_storages(
        self,
    ) -> APIResponse:
        """List all configured object storage systems."""
        action_result = await self._object_storage.list_storages.wait_for_complete(
            ListObjectStorageAction()
        )

        storage_responses = [storage_data.to_dto() for storage_data in action_result.data]

        resp = ObjectStorageListResponse(storages=storage_responses)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)
