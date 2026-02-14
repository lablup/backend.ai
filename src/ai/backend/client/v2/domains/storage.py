from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.storage.request import (
    GetPresignedDownloadURLReq,
    GetPresignedUploadURLReq,
    VFSListFilesReq,
)
from ai.backend.common.dto.manager.storage.response import (
    GetPresignedDownloadURLResponse,
    GetPresignedUploadURLResponse,
    GetVFSStorageResponse,
    ListVFSStorageResponse,
    ObjectStorageAllBucketsResponse,
    ObjectStorageBucketsResponse,
    ObjectStorageListResponse,
)
from ai.backend.common.dto.storage.response import VFSListFilesResponse


class StorageClient(BaseDomainClient):
    # ── Object storage ──────────────────────────────────────────────

    async def list_object_storages(self) -> ObjectStorageListResponse:
        return await self._client.typed_request(
            "GET",
            "/object-storages/",
            response_model=ObjectStorageListResponse,
        )

    async def get_presigned_upload_url(
        self,
        request: GetPresignedUploadURLReq,
    ) -> GetPresignedUploadURLResponse:
        return await self._client.typed_request(
            "POST",
            "/object-storages/presigned/upload",
            request=request,
            response_model=GetPresignedUploadURLResponse,
        )

    async def get_presigned_download_url(
        self,
        request: GetPresignedDownloadURLReq,
    ) -> GetPresignedDownloadURLResponse:
        return await self._client.typed_request(
            "POST",
            "/object-storages/presigned/download",
            request=request,
            response_model=GetPresignedDownloadURLResponse,
        )

    async def get_all_buckets(self) -> ObjectStorageAllBucketsResponse:
        return await self._client.typed_request(
            "GET",
            "/object-storages/buckets",
            response_model=ObjectStorageAllBucketsResponse,
        )

    async def get_buckets(self, storage_id: str) -> ObjectStorageBucketsResponse:
        return await self._client.typed_request(
            "GET",
            f"/object-storages/{storage_id}/buckets",
            response_model=ObjectStorageBucketsResponse,
        )

    # ── VFS storage ─────────────────────────────────────────────────

    async def list_vfs_storages(self) -> ListVFSStorageResponse:
        return await self._client.typed_request(
            "GET",
            "/vfs-storages/",
            response_model=ListVFSStorageResponse,
        )

    async def get_vfs_storage(self, storage_name: str) -> GetVFSStorageResponse:
        return await self._client.typed_request(
            "GET",
            f"/vfs-storages/{storage_name}",
            response_model=GetVFSStorageResponse,
        )

    async def list_vfs_files(
        self,
        storage_name: str,
        request: VFSListFilesReq,
    ) -> VFSListFilesResponse:
        return await self._client.typed_request(
            "GET",
            f"/vfs-storages/{storage_name}/files",
            request=request,
            response_model=VFSListFilesResponse,
        )
