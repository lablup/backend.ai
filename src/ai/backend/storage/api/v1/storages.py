from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING, Self, override

from aiohttp import web
from aiohttp.web_request import FileField
from pydantic import ConfigDict, Field, ValidationError

from ai.backend.common.api_handlers import (
    APIResponse,
    MiddlewareParam,
    api_handler,
)
from ai.backend.common.dto.storage.context import MultipartUploadCtx
from ai.backend.common.dto.storage.request import S3ClientOperationType, S3TokenData
from ai.backend.logging import BraceStyleAdapter
from ai.backend.storage.config.unified import ObjectStorageConfig

from ...services.storages import StoragesService
from ...utils import log_client_api_entry

if TYPE_CHECKING:
    from ...context import RootContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

_DEFAULT_CHUNKS = 8192  # Default chunk size for streaming uploads


class StoragesConfigCtx(MiddlewareParam):
    storages: list[ObjectStorageConfig]
    storage_name: str
    bucket_name: str

    @override
    @classmethod
    async def from_request(cls, request: web.Request) -> Self:
        ctx: RootContext = request.app["ctx"]
        storage_name = request.match_info.get("storage_name")
        bucket_name = request.match_info.get("bucket_name")

        if not storage_name:
            raise web.HTTPBadRequest(reason="Missing storage_name in URL path")
        if not bucket_name:
            raise web.HTTPBadRequest(reason="Missing bucket_name in URL path")

        return cls(
            storages=ctx.local_config.storages, storage_name=storage_name, bucket_name=bucket_name
        )


class TokenValidationCtx(MiddlewareParam):
    token: S3TokenData

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

            return cls(token=S3TokenData.model_validate(token_data))
        except ValidationError as e:
            raise web.HTTPBadRequest(reason="Invalid S3 token data") from e


class PrepareStreamingResponseCtx(MiddlewareParam):
    stream_response: web.StreamResponse = Field(
        ..., description="Prepared streaming response for file download"
    )

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @override
    @classmethod
    async def from_request(cls, request: web.Request) -> Self:
        stream_response = web.StreamResponse(
            status=HTTPStatus.OK,
            headers={
                "Content-Type": "application/octet-stream",
            },
        )

        await stream_response.prepare(request)
        return cls(stream_response=stream_response)


class StoragesAPIHandler:
    @api_handler
    async def upload_file(
        self,
        token_ctx: TokenValidationCtx,
        multipart_ctx: MultipartUploadCtx,
        config_ctx: StoragesConfigCtx,
    ) -> APIResponse:
        """
        Upload a file to the specified S3 bucket using streaming.
        Reads multipart file data in chunks to minimize memory usage.
        """
        token_data = token_ctx.token
        file_reader = multipart_ctx.file_reader

        await log_client_api_entry(log, "upload_file", token_data)

        if token_data.op != S3ClientOperationType.UPLOAD:
            raise web.HTTPBadRequest(reason="Invalid token operation for upload")

        storages_service = StoragesService(config_ctx.storages)

        # Read the file data as a stream
        field = await file_reader.next()

        if not isinstance(field, FileField):
            raise web.HTTPBadRequest(reason="Expected file field")

        async def data_stream():
            while True:
                chunk = await field.read_chunk(_DEFAULT_CHUNKS)
                if not chunk:
                    break
                yield chunk

        # Upload the stream using service
        response = await storages_service.stream_upload(
            config_ctx.storage_name, config_ctx.bucket_name, token_data, data_stream()
        )

        return APIResponse.build(
            status_code=HTTPStatus.OK,
            response_model=response,
        )

    @api_handler
    async def download_file(
        self,
        token_ctx: TokenValidationCtx,
        stream_response_ctx: PrepareStreamingResponseCtx,
        config_ctx: StoragesConfigCtx,
    ) -> APIResponse:
        """
        Download a file from the specified S3 bucket using streaming.
        Streams file content directly to the client without loading into memory.
        """
        token_data = token_ctx.token
        stream_response = stream_response_ctx.stream_response

        await log_client_api_entry(log, "download_file", token_data)

        if token_data.op != S3ClientOperationType.DOWNLOAD:
            raise web.HTTPBadRequest(reason="Invalid token operation for download")

        storages_service = StoragesService(config_ctx.storages)

        # Stream the file content
        async for chunk in storages_service.stream_download(
            config_ctx.storage_name, config_ctx.bucket_name, token_data
        ):
            await stream_response.write(chunk)

        return APIResponse.no_content(status_code=HTTPStatus.NO_CONTENT)

    @api_handler
    async def presigned_upload_url(
        self,
        token_ctx: TokenValidationCtx,
        config_ctx: StoragesConfigCtx,
    ) -> APIResponse:
        """
        Generate a presigned URL for uploading files directly to S3.
        Allows clients to upload files without going through the proxy server.
        """
        token_data = token_ctx.token

        await log_client_api_entry(log, "presigned_upload_url", token_data)

        if token_data.op != S3ClientOperationType.PRESIGNED_UPLOAD:
            raise web.HTTPBadRequest(reason="Invalid token operation for presigned upload")

        storages_service = StoragesService(config_ctx.storages)

        response = await storages_service.generate_presigned_upload_url(
            config_ctx.storage_name, config_ctx.bucket_name, token_data
        )

        return APIResponse.build(
            status_code=HTTPStatus.OK,
            response_model=response,
        )

    @api_handler
    async def presigned_download_url(
        self,
        token_ctx: TokenValidationCtx,
        config_ctx: StoragesConfigCtx,
    ) -> APIResponse:
        """
        Generate a presigned URL for downloading files directly from S3.
        Allows clients to download files without going through the proxy server.
        """
        token_data = token_ctx.token

        await log_client_api_entry(log, "presigned_download_url", token_data)

        if token_data.op != S3ClientOperationType.PRESIGNED_DOWNLOAD:
            raise web.HTTPBadRequest(reason="Invalid token operation for presigned download")

        storages_service = StoragesService(config_ctx.storages)

        response = await storages_service.generate_presigned_download_url(
            config_ctx.storage_name, config_ctx.bucket_name, token_data
        )

        return APIResponse.build(
            status_code=HTTPStatus.OK,
            response_model=response,
        )

    @api_handler
    async def get_file_info(
        self,
        token_ctx: TokenValidationCtx,
        config_ctx: StoragesConfigCtx,
    ) -> APIResponse:
        """
        Get metadata information about a file in S3.
        Returns file size, content type, last modified date, and ETag.
        """
        token_data = token_ctx.token

        await log_client_api_entry(log, "get_file_info", token_data)

        if token_data.op != S3ClientOperationType.INFO:
            raise web.HTTPBadRequest(reason="Invalid token operation for info")

        storages_service = StoragesService(config_ctx.storages)

        response = await storages_service.get_object_info(
            config_ctx.storage_name, config_ctx.bucket_name, token_data
        )

        return APIResponse.build(
            status_code=HTTPStatus.OK,
            response_model=response,
        )

    @api_handler
    async def delete_file(
        self,
        token_ctx: TokenValidationCtx,
        config_ctx: StoragesConfigCtx,
    ) -> APIResponse:
        """
        Delete a file from the specified S3 bucket.
        Permanently removes the object from storage.
        """
        token_data = token_ctx.token

        await log_client_api_entry(log, "delete_file", token_data)

        if token_data.op != S3ClientOperationType.DELETE:
            raise web.HTTPBadRequest(reason="Invalid token operation for delete")

        storages_service = StoragesService(config_ctx.storages)

        response = await storages_service.delete_object(
            config_ctx.storage_name, config_ctx.bucket_name, token_data
        )

        return APIResponse.build(
            status_code=HTTPStatus.OK,
            response_model=response,
        )


def create_app(ctx: RootContext) -> web.Application:
    app = web.Application()
    app["ctx"] = ctx
    app["prefix"] = "v1/storages"

    api_handler = StoragesAPIHandler()
    app.router.add_route(
        "GET", "/s3/{storage_name}/buckets/{bucket_name}/files", api_handler.get_file_info
    )
    app.router.add_route(
        "DELETE", "/s3/{storage_name}/buckets/{bucket_name}/files", api_handler.delete_file
    )
    app.router.add_route(
        "POST", "/s3/{storage_name}/buckets/{bucket_name}/files/upload", api_handler.upload_file
    )
    app.router.add_route(
        "GET", "/s3/{storage_name}/buckets/{bucket_name}/files/download", api_handler.download_file
    )
    app.router.add_route(
        "POST",
        "/s3/{storage_name}/buckets/{bucket_name}/files/presigned/upload",
        api_handler.presigned_upload_url,
    )
    app.router.add_route(
        "GET",
        "/s3/{storage_name}/buckets/{bucket_name}/files/presigned/download",
        api_handler.presigned_download_url,
    )

    return app
