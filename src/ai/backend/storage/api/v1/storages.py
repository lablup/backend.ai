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

if TYPE_CHECKING:
    from ...context import RootContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

_DEFAULT_CHUNKS = 8192  # Default chunk size for streaming uploads


class StoragesConfigCtx(MiddlewareParam):
    storages: list[ObjectStorageConfig]

    @override
    @classmethod
    async def from_request(cls, request: web.Request) -> Self:
        ctx: RootContext = request.app["ctx"]
        return cls(storages=ctx.local_config.storages)


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
        """Upload a file to S3 using streaming."""
        token_data = token_ctx.token
        file_reader = multipart_ctx.file_reader

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
        response = await storages_service.stream_upload(token_data, data_stream())

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
        """Download a file from S3."""
        token_data = token_ctx.token
        stream_response = stream_response_ctx.stream_response

        if token_data.op != S3ClientOperationType.DOWNLOAD:
            raise web.HTTPBadRequest(reason="Invalid token operation for download")

        storages_service = StoragesService(config_ctx.storages)

        # Stream the file content
        async for chunk in storages_service.stream_download(token_data):
            await stream_response.write(chunk)

        return APIResponse.no_content(status_code=HTTPStatus.NO_CONTENT)

    @api_handler
    async def presigned_upload_url(
        self,
        token_ctx: TokenValidationCtx,
        config_ctx: StoragesConfigCtx,
    ) -> APIResponse:
        """Generate presigned upload URL"""
        token_data = token_ctx.token
        if token_data.op != S3ClientOperationType.PRESIGNED_UPLOAD:
            raise web.HTTPBadRequest(reason="Invalid token operation for presigned upload")

        storages_service = StoragesService(config_ctx.storages)
        response = await storages_service.generate_presigned_upload_url(token_data)

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
        """Generate presigned download URL"""
        token_data = token_ctx.token
        if token_data.op != S3ClientOperationType.PRESIGNED_DOWNLOAD:
            raise web.HTTPBadRequest(reason="Invalid token operation for presigned download")

        storages_service = StoragesService(config_ctx.storages)
        response = await storages_service.generate_presigned_download_url(token_data)

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
        """Get file information"""
        token_data = token_ctx.token
        if token_data.op != S3ClientOperationType.INFO:
            raise web.HTTPBadRequest(reason="Invalid token operation for info")

        storages_service = StoragesService(config_ctx.storages)
        response = await storages_service.get_object_info(token_data)

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
        """Delete object"""
        token_data = token_ctx.token
        if token_data.op != S3ClientOperationType.DELETE:
            raise web.HTTPBadRequest(reason="Invalid token operation for delete")

        storages_service = StoragesService(config_ctx.storages)
        response = await storages_service.delete_object(token_data)

        return APIResponse.build(
            status_code=HTTPStatus.OK,
            response_model=response,
        )


def create_app(ctx: RootContext) -> web.Application:
    app = web.Application()
    app["ctx"] = ctx
    app["prefix"] = "v1/storages"

    api_handler = StoragesAPIHandler()
    app.router.add_route("GET", "/s3/files", api_handler.get_file_info)
    app.router.add_route("DELETE", "/s3/files", api_handler.delete_file)
    app.router.add_route("POST", "/s3/files/upload", api_handler.upload_file)
    app.router.add_route("GET", "/s3/files/download", api_handler.download_file)
    app.router.add_route("POST", "/s3/files/presigned/upload", api_handler.presigned_upload_url)
    app.router.add_route("GET", "/s3/files/presigned/download", api_handler.presigned_download_url)

    return app
