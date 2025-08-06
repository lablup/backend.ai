from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING, Generic, Self, Type, TypeVar, override

from aiohttp import web
from pydantic import ValidationError

from ai.backend.common.api_handlers import (
    APIResponse,
    APIStreamResponse,
    BaseRequestModel,
    MiddlewareParam,
    PathParam,
    api_handler,
    stream_api_handler,
)
from ai.backend.common.dto.storage.context import MultipartUploadCtx
from ai.backend.common.dto.storage.request import (
    DeleteFileReq,
    DownloadFileReq,
    GetFileMetaReq,
    ObjectStorageAPIPathParams,
    PresignedDownloadReq,
    PresignedUploadReq,
    UploadFileReq,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.storage.config.unified import ObjectStorageConfig

from ...services.storages import StoragesService
from ...utils import log_client_api_entry

if TYPE_CHECKING:
    from ...context import RootContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

_DEFAULT_UPLOAD_FILE_CHUNKS = 8192  # Default chunk size for streaming uploads


class StoragesConfigCtx(MiddlewareParam):
    storages: list[ObjectStorageConfig]

    @override
    @classmethod
    async def from_request(cls, request: web.Request) -> Self:
        ctx: RootContext = request.app["ctx"]

        return cls(storages=ctx.local_config.storages)


TReq = TypeVar("TReq", bound=BaseRequestModel)


class RequestValidationCtx(MiddlewareParam, Generic[TReq]):
    data: TReq

    @classmethod
    def _resolve_req_type(cls) -> Type[TReq]:
        meta = cls.__pydantic_generic_metadata__
        return meta["args"][0]

    @override
    @classmethod
    async def from_request(cls, request: web.Request) -> Self:
        import jwt

        try:
            ctx: RootContext = request.app["ctx"]
            secret = ctx.local_config.storage_proxy.secret
            raw_params = dict(request.query)
            if "token" not in raw_params:
                raise web.HTTPBadRequest(reason="Missing 'token' query parameter")

            token = raw_params["token"]
            if not isinstance(token, str):
                raise web.HTTPBadRequest(reason="'token' must be a string")
            try:
                token_data = jwt.decode(token, secret, algorithms=["HS256"])
            except jwt.PyJWTError as e:
                raise web.HTTPUnauthorized(reason=f"Invalid JWT token: {str(e)}") from e

            ReqModel = cls._resolve_req_type()
            return cls(data=ReqModel.model_validate(token_data))
        except ValidationError as e:
            raise web.HTTPBadRequest(reason="Invalid S3 token data") from e


class StoragesAPIHandler:
    @api_handler
    async def upload_file(
        self,
        path: PathParam[ObjectStorageAPIPathParams],
        request_ctx: RequestValidationCtx[UploadFileReq],
        multipart_ctx: MultipartUploadCtx,
        config_ctx: StoragesConfigCtx,
    ) -> APIResponse:
        """
        Upload a file to the specified S3 bucket using streaming.
        Reads multipart file data in chunks to minimize memory usage.
        """
        req = request_ctx.data
        content_type = req.content_type
        content_length = req.content_length
        filepath = req.key
        file_reader = multipart_ctx.file_reader
        storage_name = path.parsed.storage_name
        bucket_name = path.parsed.bucket_name

        await log_client_api_entry(log, "upload_file", req)

        storages_service = StoragesService(config_ctx.storages)

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

        response = await storages_service.stream_upload(
            storage_name, bucket_name, filepath, content_type, content_length, data_stream()
        )

        return APIResponse.build(
            status_code=HTTPStatus.OK,
            response_model=response,
        )

    @stream_api_handler
    async def download_file(
        self,
        path: PathParam[ObjectStorageAPIPathParams],
        request_ctx: RequestValidationCtx[DownloadFileReq],
        config_ctx: StoragesConfigCtx,
    ) -> APIStreamResponse:
        """
        Download a file from the specified S3 bucket using streaming.
        Streams file content directly to the client without loading into memory.
        """
        req = request_ctx.data
        filepath = req.key
        storage_name = path.parsed.storage_name
        bucket_name = path.parsed.bucket_name

        await log_client_api_entry(log, "download_file", req)
        storages_service = StoragesService(config_ctx.storages)
        download_stream = storages_service.stream_download(storage_name, bucket_name, filepath)

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
        request_ctx: RequestValidationCtx[PresignedUploadReq],
        config_ctx: StoragesConfigCtx,
    ) -> APIResponse:
        """
        Generate a presigned URL for uploading files directly to S3.
        Allows clients to upload files without going through the proxy server.
        """
        req = request_ctx.data
        storage_name = path.parsed.storage_name
        bucket_name = path.parsed.bucket_name

        await log_client_api_entry(log, "presigned_upload_url", req)
        storages_service = StoragesService(config_ctx.storages)
        response = await storages_service.generate_presigned_upload_url(
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
        request_ctx: RequestValidationCtx[PresignedDownloadReq],
        config_ctx: StoragesConfigCtx,
    ) -> APIResponse:
        """
        Generate a presigned URL for downloading files directly from S3.
        Allows clients to download files without going through the proxy server.
        """
        req = request_ctx.data
        filepath = req.key
        storage_name = path.parsed.storage_name
        bucket_name = path.parsed.bucket_name

        await log_client_api_entry(log, "presigned_download_url", req)
        storages_service = StoragesService(config_ctx.storages)
        response = await storages_service.generate_presigned_download_url(
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
        request_ctx: RequestValidationCtx[GetFileMetaReq],
        config_ctx: StoragesConfigCtx,
    ) -> APIResponse:
        """
        Get metadata information about a file in S3.
        Returns file size, content type, last modified date, and ETag.
        """
        req = request_ctx.data
        filepath = req.key
        storage_name = path.parsed.storage_name
        bucket_name = path.parsed.bucket_name

        await log_client_api_entry(log, "get_file_meta", req)

        storages_service = StoragesService(config_ctx.storages)
        response = await storages_service.get_object_info(storage_name, bucket_name, filepath)

        return APIResponse.build(
            status_code=HTTPStatus.OK,
            response_model=response,
        )

    @api_handler
    async def delete_file(
        self,
        path: PathParam[ObjectStorageAPIPathParams],
        request_ctx: RequestValidationCtx[DeleteFileReq],
        config_ctx: StoragesConfigCtx,
    ) -> APIResponse:
        """
        Delete a file from the specified S3 bucket.
        Permanently removes the object from storage.
        """
        req = request_ctx.data
        filepath = req.key
        storage_name = path.parsed.storage_name
        bucket_name = path.parsed.bucket_name

        await log_client_api_entry(log, "delete_file", req)
        storages_service = StoragesService(config_ctx.storages)
        response = await storages_service.delete_file(storage_name, bucket_name, filepath)

        return APIResponse.build(
            status_code=HTTPStatus.OK,
            response_model=response,
        )


def create_app(ctx: RootContext) -> web.Application:
    app = web.Application()
    app["ctx"] = ctx
    app["prefix"] = "v1/storages"

    # TODO: Add bucket creation and deletion endpoints when working Manager integration
    api_handler = StoragesAPIHandler()
    app.router.add_route(
        "GET", "/s3/{storage_name}/buckets/{bucket_name}/file/meta", api_handler.get_file_meta
    )
    app.router.add_route(
        "DELETE", "/s3/{storage_name}/buckets/{bucket_name}/file", api_handler.delete_file
    )
    app.router.add_route(
        "POST", "/s3/{storage_name}/buckets/{bucket_name}/file/upload", api_handler.upload_file
    )
    app.router.add_route(
        "GET", "/s3/{storage_name}/buckets/{bucket_name}/file/download", api_handler.download_file
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
