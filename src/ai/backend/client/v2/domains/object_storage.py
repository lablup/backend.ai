from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.object_storage.request import (
    GetPresignedDownloadURLReq,
    GetPresignedUploadURLReq,
)
from ai.backend.common.dto.manager.object_storage.response import (
    GetPresignedDownloadURLResponse,
    GetPresignedUploadURLResponse,
    ObjectStorageAllBucketsResponse,
    ObjectStorageBucketsResponse,
    ObjectStorageListResponse,
)


class ObjectStorageClient(BaseDomainClient):
    API_PREFIX = "/object-storages"

    # ── List / query ──────────────────────────────────────────────

    async def list(self) -> ObjectStorageListResponse:
        return await self._client.typed_request(
            "GET",
            f"{self.API_PREFIX}/",
            response_model=ObjectStorageListResponse,
        )

    async def get_all_buckets(self) -> ObjectStorageAllBucketsResponse:
        return await self._client.typed_request(
            "GET",
            f"{self.API_PREFIX}/buckets",
            response_model=ObjectStorageAllBucketsResponse,
        )

    async def get_buckets(self, storage_id: str) -> ObjectStorageBucketsResponse:
        return await self._client.typed_request(
            "GET",
            f"{self.API_PREFIX}/{storage_id}/buckets",
            response_model=ObjectStorageBucketsResponse,
        )

    # ── Presigned URLs ────────────────────────────────────────────

    async def get_presigned_upload_url(
        self,
        request: GetPresignedUploadURLReq,
    ) -> GetPresignedUploadURLResponse:
        return await self._client.typed_request(
            "POST",
            f"{self.API_PREFIX}/presigned/upload",
            request=request,
            response_model=GetPresignedUploadURLResponse,
        )

    async def get_presigned_download_url(
        self,
        request: GetPresignedDownloadURLReq,
    ) -> GetPresignedDownloadURLResponse:
        return await self._client.typed_request(
            "POST",
            f"{self.API_PREFIX}/presigned/download",
            request=request,
            response_model=GetPresignedDownloadURLResponse,
        )
