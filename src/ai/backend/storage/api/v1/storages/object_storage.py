from __future__ import annotations

import logging
import mimetypes
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
from ai.backend.storage.types import MultipartFileUploadStreamReader

from ....services.storages.object_storage import ObjectStorageService
from ....utils import log_client_api_entry

if TYPE_CHECKING:
    from ....context import RootContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ObjectStorageAPIHandler:
    _object_storage_service: ObjectStorageService

    def __init__(
        self,
        object_storage_service: ObjectStorageService,
    ) -> None:
        self._object_storage_service = object_storage_service

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
        filepath = req.key
        file_reader = multipart_ctx.file_reader
        storage_name = path.parsed.storage_name
        bucket_name = path.parsed.bucket_name

        await log_client_api_entry(log, "upload_object", req)

        # Determine content type: use header if available, otherwise guess from filename
        content_type = multipart_ctx.content_type
        if not content_type:
            content_type, _ = mimetypes.guess_type(filepath)

        upload_stream = MultipartFileUploadStreamReader(file_reader, content_type)

        await self._object_storage_service.stream_upload(
            storage_name, bucket_name, filepath, upload_stream
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
        file_stream = await self._object_storage_service.stream_download(
            storage_name, bucket_name, filepath
        )

        return APIStreamResponse(
            body=file_stream,
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
        response = await self._object_storage_service.generate_presigned_upload_url(
            storage_name, bucket_name, req.key
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
        response = await self._object_storage_service.generate_presigned_download_url(
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

        response = await self._object_storage_service.get_object_info(
            storage_name, bucket_name, filepath
        )

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

        await self._object_storage_service.delete_object(storage_name, bucket_name, prefix)

        return APIResponse.no_content(
            status_code=HTTPStatus.NO_CONTENT,
        )


def create_app(ctx: RootContext) -> web.Application:
    app = web.Application()
    app["ctx"] = ctx
    app["prefix"] = "v1/storages/s3"

    object_storage_service = ObjectStorageService(ctx.storage_pool)
    api_handler = ObjectStorageAPIHandler(
        object_storage_service=object_storage_service,
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
