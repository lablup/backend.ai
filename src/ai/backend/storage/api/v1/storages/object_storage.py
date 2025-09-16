from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING

from aiohttp import web

from ai.backend.common.api_handlers import (
    APIResponse,
    APIStreamResponse,
    BodyParam,
    PathParam,
    api_handler,
    stream_api_handler,
)
from ai.backend.common.dto.storage.context import MultipartUploadCtx
from ai.backend.common.dto.storage.request import (
    DeleteObjectReq,
    DownloadObjectReq,
    GetObjectMetaReq,
    ObjectStorageAPIPathParams,
    PresignedDownloadObjectReq,
    PresignedUploadObjectReq,
    UploadObjectReq,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.storage.config.unified import (
    ObjectStorageConfig,
)

from ....services.storages.object_storage import ObjectStorageService
from ....utils import log_client_api_entry

if TYPE_CHECKING:
    from ....context import RootContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

_DEFAULT_UPLOAD_FILE_CHUNKS = 8192  # Default chunk size for streaming uploads


class ObjectStorageAPIHandler:
    _storage_configs: list[ObjectStorageConfig]

    def __init__(
        self,
        storage_configs: list[ObjectStorageConfig],
    ) -> None:
        self._storage_configs = storage_configs

    @api_handler
    async def upload_object(
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

        await log_client_api_entry(log, "upload_object", req)

        storage_service = ObjectStorageService(self._storage_configs)

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

        await storage_service.stream_upload(
            storage_name, bucket_name, filepath, content_type, data_stream()
        )

        return APIResponse.no_content(
            status_code=HTTPStatus.NO_CONTENT,
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
        storage_service = ObjectStorageService(self._storage_configs)
        download_stream = storage_service.stream_download(storage_name, bucket_name, filepath)

        return APIStreamResponse(
            body=download_stream,
            status=HTTPStatus.OK,
            headers={
                "Content-Type": "application/octet-stream",
            },
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
        storage_service = ObjectStorageService(self._storage_configs)
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
        storage_service = ObjectStorageService(self._storage_configs)
        response = await storage_service.generate_presigned_download_url(
            storage_name, bucket_name, filepath
        )

        return APIResponse.build(
            status_code=HTTPStatus.OK,
            response_model=response,
        )

    @api_handler
    async def get_object_meta(
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

        await log_client_api_entry(log, "get_object_meta", req)

        storage_service = ObjectStorageService(self._storage_configs)
        response = await storage_service.get_object_info(storage_name, bucket_name, filepath)

        return APIResponse.build(
            status_code=HTTPStatus.OK,
            response_model=response,
        )

    @api_handler
    async def delete_object(
        self,
        path: PathParam[ObjectStorageAPIPathParams],
        body: BodyParam[DeleteObjectReq],
    ) -> APIResponse:
        """
        Delete an object and its contents from the specified S3 bucket.
        Permanently removes the object from storage.
        """
        req = body.parsed
        prefix = req.key
        storage_name = path.parsed.storage_name
        bucket_name = path.parsed.bucket_name

        await log_client_api_entry(log, "delete_object", req)
        storage_service = ObjectStorageService(self._storage_configs)

        await storage_service.delete_object(storage_name, bucket_name, prefix)

        return APIResponse.no_content(
            status_code=HTTPStatus.NO_CONTENT,
        )


def create_app(ctx: RootContext) -> web.Application:
    app = web.Application()
    app["ctx"] = ctx
    app["prefix"] = "v1/storages/s3"

    api_handler = ObjectStorageAPIHandler(
        storage_configs=ctx.local_config.storages,
    )
    app.router.add_route(
        "GET", "/{storage_name}/buckets/{bucket_name}/object/meta", api_handler.get_object_meta
    )
    app.router.add_route(
        "DELETE", "/{storage_name}/buckets/{bucket_name}/object", api_handler.delete_object
    )
    app.router.add_route(
        "POST", "/{storage_name}/buckets/{bucket_name}/object/upload", api_handler.upload_object
    )
    app.router.add_route(
        "POST",
        "/{storage_name}/buckets/{bucket_name}/object/download",
        api_handler.download_file,
    )
    app.router.add_route(
        "POST",
        "/{storage_name}/buckets/{bucket_name}/object/presigned/upload",
        api_handler.presigned_upload_url,
    )
    app.router.add_route(
        "POST",
        "/{storage_name}/buckets/{bucket_name}/object/presigned/download",
        api_handler.presigned_download_url,
    )

    return app
