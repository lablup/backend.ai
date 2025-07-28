"""
S3 Storage API endpoints for file upload/download operations
"""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING

import trafaret as t
from aiohttp import web
from aiohttp.web_request import FileField
from pydantic import ValidationError

from ai.backend.common import validators as tx
from ai.backend.common.dto.storage.request import S3TokenData
from ai.backend.common.dto.storage.response import (
    ErrorResponse,
)
from ai.backend.common.json import dump_json_str
from ai.backend.logging import BraceStyleAdapter

from ..exception import (
    PresignedDownloadURLGenerationError,
    PresignedUploadURLGenerationError,
    StorageProxyError,
)
from ..services.storages import StoragesService

if TYPE_CHECKING:
    from ..context import RootContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

_DEFAULT_CHUNKS = 8192  # Default chunk size for streaming uploads

s3_token_data_iv = t.Dict(
    {
        t.Key("op"): t.Enum(
            "upload", "download", "info", "delete", "presigned_upload", "presigned_download"
        ),
        t.Key("bucket"): t.String(),
        t.Key("key"): t.String(),
        t.Key("expiration", optional=True): t.Int(gt=0, lte=604800),
        t.Key("content_type", optional=True): t.String(),
        t.Key("min_size", optional=True): t.Int(gte=0),
        t.Key("max_size", optional=True): t.Int(gt=0),
        t.Key("filename", optional=True): t.String(),
    },
).allow_extra("*")  # allow JWT-intrinsic keys


# TODO: Move pydantic_params_api_handler, pydantic_response_api_handler into common and use them here
async def validate_token_request(request: web.Request) -> S3TokenData:
    """Helper function to validate JWT token and return S3TokenData."""
    ctx: RootContext = request.app["ctx"]
    secret = ctx.local_config.storage_proxy.secret

    try:
        raw_params = dict(request.query)
        if "token" not in raw_params:
            raise web.HTTPBadRequest(text="Missing token parameter")

        token_validator = tx.JsonWebToken(secret=secret, inner_iv=s3_token_data_iv)
        decoded_token = token_validator.check(raw_params["token"])
        return S3TokenData(**decoded_token)

    except ValidationError as e:
        log.debug("pydantic validation error", exc_info=e)
        raise web.HTTPBadRequest(
            text=dump_json_str({
                "type": "https://api.backend.ai/probs/storage/invalid-api-params",
                "title": "Invalid API parameters",
                "data": e.errors(),
            }),
            content_type="application/problem+json",
        )
    except t.DataError as e:
        log.debug("JWT decode error", exc_info=e)
        raise web.HTTPBadRequest(
            text=dump_json_str({
                "type": "https://api.backend.ai/probs/storage/invalid-api-params",
                "title": "Invalid JWT token",
                "data": e.as_dict(),
            }),
            content_type="application/problem+json",
        )


async def stream_upload(request: web.Request) -> web.Response:
    """Upload a file to S3 using streaming."""
    token_data = await validate_token_request(request)
    if token_data.op != "upload":
        raise web.HTTPBadRequest(reason="Invalid token operation for upload")

    try:
        ctx: RootContext = request.app["ctx"]
        storages_service = StoragesService(ctx.local_config.storages)

        # Read the file data as a stream
        reader = await request.multipart()
        field = await reader.next()

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

        return web.Response(
            status=HTTPStatus.OK,
            body=dump_json_str(response.model_dump()),
            content_type="application/json",
        )

    except StorageProxyError as e:
        error_response = ErrorResponse(error=str(e))
        return web.Response(
            status=HTTPStatus.INTERNAL_SERVER_ERROR,
            body=dump_json_str(error_response.model_dump()),
            content_type="application/json",
        )


async def presigned_upload_url(request: web.Request) -> web.Response:
    """Generate presigned upload URL"""
    token_data = await validate_token_request(request)
    if token_data.op != "presigned_upload":
        raise web.HTTPBadRequest(reason="Invalid token operation for presigned upload")

    try:
        ctx: RootContext = request.app["ctx"]
        storages_service = StoragesService(ctx.local_config.storages)

        response = await storages_service.generate_presigned_upload_url(token_data)

        return web.Response(
            status=HTTPStatus.OK,
            body=dump_json_str(response.model_dump()),
            content_type="application/json",
        )

    except PresignedUploadURLGenerationError as e:
        error_response = ErrorResponse(error=f"Presigned upload URL generation failed: {str(e)}")
        return web.Response(
            status=HTTPStatus.INTERNAL_SERVER_ERROR,
            body=dump_json_str(error_response.model_dump()),
            content_type="application/json",
        )


async def presigned_download_url(request: web.Request) -> web.Response:
    """Generate presigned download URL"""
    token_data = await validate_token_request(request)
    if token_data.op != "presigned_download":
        raise web.HTTPBadRequest(reason="Invalid token operation for presigned download")

    try:
        ctx: RootContext = request.app["ctx"]
        storages_service = StoragesService(ctx.local_config.storages)

        response = await storages_service.generate_presigned_download_url(token_data)

        return web.Response(
            status=HTTPStatus.OK,
            body=dump_json_str(response.model_dump()),
            content_type="application/json",
        )

    except PresignedDownloadURLGenerationError as e:
        error_response = ErrorResponse(error=f"Presigned download URL generation failed: {str(e)}")
        return web.Response(
            status=HTTPStatus.INTERNAL_SERVER_ERROR,
            body=dump_json_str(error_response.model_dump()),
            content_type="application/json",
        )


async def get_object_info(request: web.Request) -> web.Response:
    """Get object information"""
    token_data = await validate_token_request(request)
    if token_data.op != "info":
        raise web.HTTPBadRequest(reason="Invalid token operation for info")

    try:
        ctx: RootContext = request.app["ctx"]
        storages_service = StoragesService(ctx.local_config.storages)

        response = await storages_service.get_object_info(token_data)

        return web.Response(
            status=HTTPStatus.OK,
            body=dump_json_str(response.model_dump()),
            content_type="application/json",
        )

    except Exception as e:
        log.error(f"Get object info failed: {e}")
        error_response = ErrorResponse(error=f"Get object info failed: {str(e)}")
        return web.Response(
            status=HTTPStatus.INTERNAL_SERVER_ERROR,
            body=dump_json_str(error_response.model_dump()),
            content_type="application/json",
        )


async def delete_object(request: web.Request) -> web.Response:
    """Delete object"""
    token_data = await validate_token_request(request)
    if token_data.op != "delete":
        raise web.HTTPBadRequest(reason="Invalid token operation for delete")

    try:
        ctx: RootContext = request.app["ctx"]
        storages_service = StoragesService(ctx.local_config.storages)

        response = await storages_service.delete_object(token_data)

        return web.Response(
            status=HTTPStatus.OK,
            body=dump_json_str(response.model_dump()),
            content_type="application/json",
        )

    except Exception as e:
        log.error(f"Delete object failed: {e}")
        error_response = ErrorResponse(error=f"Delete object failed: {str(e)}")
        return web.Response(
            status=HTTPStatus.INTERNAL_SERVER_ERROR,
            body=dump_json_str(error_response.model_dump()),
            content_type="application/json",
        )


def create_app(ctx: RootContext) -> web.Application:
    app = web.Application()
    app["ctx"] = ctx
    app["prefix"] = "storages"

    # Route definitions following the pattern from manager.py
    app.router.add_route("POST", "/s3/upload", stream_upload)
    app.router.add_route("POST", "/s3/presigned-upload-url", presigned_upload_url)
    app.router.add_route("GET", "/s3/presigned-download-url", presigned_download_url)
    app.router.add_route("GET", "/s3", get_object_info)
    app.router.add_route("DELETE", "/s3", delete_object)

    return app
