from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING, cast

from aiohttp import web

from ai.backend.common.api_handlers import (
    APIResponse,
    APIStreamResponse,
    BodyParam,
    PathParam,
    api_handler,
    stream_api_handler,
)
from ai.backend.common.bgtask.bgtask import BackgroundTaskManager
from ai.backend.common.bgtask.reporter import ProgressReporter
from ai.backend.common.dto.storage.context import MultipartUploadCtx
from ai.backend.common.dto.storage.request import (
    DeleteObjectReq,
    DownloadObjectReq,
    GetObjectMetaReq,
    ObjectStorageAPIPathParams,
    PresignedDownloadObjectReq,
    PresignedUploadObjectReq,
    PullObjectReq,
    UploadObjectReq,
)
from ai.backend.common.dto.storage.response import PullObjectResponse
from ai.backend.logging import BraceStyleAdapter
from ai.backend.storage.config.unified import (
    ArtifactRegistryConfig,
    ObjectStorageConfig,
    ReservoirConfig,
)
from ai.backend.storage.exception import ReservoirStorageConfigInvalidError
from ai.backend.storage.types import BucketCopyOptions

from ...services.storages import StorageService
from ...utils import log_client_api_entry

if TYPE_CHECKING:
    from ...context import RootContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

_DEFAULT_UPLOAD_FILE_CHUNKS = 8192  # Default chunk size for streaming uploads


class StorageAPIHandler:
    _storage_configs: list[ObjectStorageConfig]
    _registry_configs: list[ArtifactRegistryConfig]
    _background_task_manager: BackgroundTaskManager

    def __init__(
        self,
        storage_configs: list[ObjectStorageConfig],
        registry_configs: list[ArtifactRegistryConfig],
        background_task_manager: BackgroundTaskManager,
    ) -> None:
        self._storage_configs = storage_configs
        self._registry_configs = registry_configs
        self._background_task_manager = background_task_manager

    @api_handler
    async def upload_file(
        self,
        path: PathParam[ObjectStorageAPIPathParams],
        body: BodyParam[UploadObjectReq],
        multipart_ctx: MultipartUploadCtx,
    ) -> APIResponse:
        """
        Upload a file to the specified S3 bucket using streaming.
        Reads multipart file data in chunks to minimize memory usage.
        """
        req = body.parsed
        content_type = req.content_type
        filepath = req.key
        file_reader = multipart_ctx.file_reader
        storage_name = path.parsed.storage_name
        bucket_name = path.parsed.bucket_name

        await log_client_api_entry(log, "upload_file", req)

        storage_service = StorageService(self._storage_configs)

        file_part = await file_reader.next()
        while file_part and not getattr(file_part, "filename", None):
            await file_part.release()
            file_part = await file_reader.next()

        if file_part is None:
            raise web.HTTPBadRequest(reason='No file part found (expected field "file")')

        async def data_stream():
            while True:
                chunk = await file_part.read_chunk(_DEFAULT_UPLOAD_FILE_CHUNKS)
                if not chunk:
                    break
                yield chunk

        response = await storage_service.stream_upload(
            storage_name, bucket_name, filepath, content_type, data_stream()
        )

        return APIResponse.build(
            status_code=HTTPStatus.OK,
            response_model=response,
        )

    @stream_api_handler
    async def download_file(
        self,
        path: PathParam[ObjectStorageAPIPathParams],
        body: BodyParam[DownloadObjectReq],
    ) -> APIStreamResponse:
        """
        Download a file from the specified S3 bucket using streaming.
        Streams file content directly to the client without loading into memory.
        """
        req = body.parsed
        filepath = req.key
        storage_name = path.parsed.storage_name
        bucket_name = path.parsed.bucket_name

        await log_client_api_entry(log, "download_file", req)
        storage_service = StorageService(self._storage_configs)
        download_stream = storage_service.stream_download(storage_name, bucket_name, filepath)

        return APIStreamResponse(
            body=download_stream,
            status=HTTPStatus.OK,
            headers={
                "Content-Type": "application/octet-stream",
            },
        )

    @api_handler
    async def pull_bucket(
        self,
        path: PathParam[ObjectStorageAPIPathParams],
        body: BodyParam[PullObjectReq],
    ) -> APIResponse:
        """
        Pull a file from URL and store it in the specified S3 bucket.
        Downloads file content from URL and uploads it to storage using streaming.
        """
        req = body.parsed
        await log_client_api_entry(log, "pull_file", req)

        storage_name = path.parsed.storage_name
        bucket_name = path.parsed.bucket_name

        reservoir_configs = list(
            filter(lambda r: isinstance(r.config, ReservoirConfig), self._registry_configs)
        )

        if len(reservoir_configs) == 0:
            raise ReservoirStorageConfigInvalidError("No reservoir registry configuration found.")

        # For now, we only use the first reservoir registry configuration
        reservoir_config: ReservoirConfig = cast(ReservoirConfig, reservoir_configs[0].config)

        async def _pull_task(reporter: ProgressReporter) -> None:
            if (
                not reservoir_config.object_storage_access_key
                or not reservoir_config.object_storage_secret_key
            ):
                raise ReservoirStorageConfigInvalidError(
                    "Reservoir registry is not properly configured for object storage access."
                )

            storage_service = StorageService(self._storage_configs)

            await storage_service.stream_bucket_to_bucket(
                src=reservoir_config,
                storage_name=storage_name,
                bucket_name=bucket_name,
                options=BucketCopyOptions(concurrency=16),
                progress_reporter=reporter,
            )

        task_id = await self._background_task_manager.start(_pull_task)

        return APIResponse.build(
            status_code=HTTPStatus.ACCEPTED, response_model=PullObjectResponse(task_id=task_id)
        )

    @api_handler
    async def presigned_upload_url(
        self,
        path: PathParam[ObjectStorageAPIPathParams],
        body: BodyParam[PresignedUploadObjectReq],
    ) -> APIResponse:
        """
        Generate a presigned URL for uploading files directly to S3.
        Allows clients to upload files without going through the proxy server.
        """
        req = body.parsed
        storage_name = path.parsed.storage_name
        bucket_name = path.parsed.bucket_name

        await log_client_api_entry(log, "presigned_upload_url", req)
        storage_service = StorageService(self._storage_configs)
        response = await storage_service.generate_presigned_upload_url(
            storage_name, bucket_name, req
        )

        return APIResponse.build(
            status_code=HTTPStatus.OK,
            response_model=response,
        )

    @api_handler
    async def presigned_download_url(
        self,
        path: PathParam[ObjectStorageAPIPathParams],
        body: BodyParam[PresignedDownloadObjectReq],
    ) -> APIResponse:
        """
        Generate a presigned URL for downloading files directly from S3.
        Allows clients to download files without going through the proxy server.
        """
        req = body.parsed
        filepath = req.key
        storage_name = path.parsed.storage_name
        bucket_name = path.parsed.bucket_name

        await log_client_api_entry(log, "presigned_download_url", req)
        storage_service = StorageService(self._storage_configs)
        response = await storage_service.generate_presigned_download_url(
            storage_name, bucket_name, filepath
        )

        return APIResponse.build(
            status_code=HTTPStatus.OK,
            response_model=response,
        )

    @api_handler
    async def get_file_meta(
        self,
        path: PathParam[ObjectStorageAPIPathParams],
        body: BodyParam[GetObjectMetaReq],
    ) -> APIResponse:
        """
        Get metadata information about a file in S3.
        Returns file size, content type, last modified date, and ETag.
        """
        req = body.parsed
        filepath = req.key
        storage_name = path.parsed.storage_name
        bucket_name = path.parsed.bucket_name

        await log_client_api_entry(log, "get_file_meta", req)

        storage_service = StorageService(self._storage_configs)
        response = await storage_service.get_object_info(storage_name, bucket_name, filepath)

        return APIResponse.build(
            status_code=HTTPStatus.OK,
            response_model=response,
        )

    @api_handler
    async def delete_folder(
        self,
        path: PathParam[ObjectStorageAPIPathParams],
        body: BodyParam[DeleteObjectReq],
    ) -> APIResponse:
        """
        Delete a folder and its contents from the specified S3 bucket.
        Permanently removes the object from storage.
        """
        req = body.parsed
        prefix = req.key
        storage_name = path.parsed.storage_name
        bucket_name = path.parsed.bucket_name

        await log_client_api_entry(log, "delete_folder", req)
        storage_service = StorageService(self._storage_configs)

        response = await storage_service.delete_folder(storage_name, bucket_name, prefix)

        return APIResponse.build(
            status_code=HTTPStatus.OK,
            response_model=response,
        )


def create_app(ctx: RootContext) -> web.Application:
    app = web.Application()
    app["ctx"] = ctx
    app["prefix"] = "v1/storages"

    # TODO: Add bucket creation and deletion endpoints when working Manager integration
    api_handler = StorageAPIHandler(
        storage_configs=ctx.local_config.storages,
        registry_configs=ctx.local_config.registries,
        background_task_manager=ctx.background_task_manager,
    )
    app.router.add_route(
        "GET", "/s3/{storage_name}/buckets/{bucket_name}/file/meta", api_handler.get_file_meta
    )
    app.router.add_route(
        "DELETE", "/s3/{storage_name}/buckets/{bucket_name}/file", api_handler.delete_folder
    )
    app.router.add_route(
        "POST", "/s3/{storage_name}/buckets/{bucket_name}/file/upload", api_handler.upload_file
    )
    app.router.add_route(
        "GET", "/s3/{storage_name}/buckets/{bucket_name}/file/download", api_handler.download_file
    )
    app.router.add_route(
        "POST", "/s3/{storage_name}/buckets/{bucket_name}/file/pull", api_handler.pull_bucket
    )
    app.router.add_route(
        "POST",
        "/s3/{storage_name}/buckets/{bucket_name}/file/presigned/upload",
        api_handler.presigned_upload_url,
    )
    app.router.add_route(
        "GET",
        "/s3/{storage_name}/buckets/{bucket_name}/file/presigned/download",
        api_handler.presigned_download_url,
    )

    return app
