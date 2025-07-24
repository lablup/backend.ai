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
    DeleteResponse,
    ErrorResponse,
    ObjectInfoResponse,
    PresignedDownloadResponse,
    PresignedUploadResponse,
    UploadResponse,
)
from ai.backend.common.json import dump_json_str
from ai.backend.logging import BraceStyleAdapter

from ..client.s3 import S3Client
from ..exception import (
    PresignedDownloadURLGenerationError,
    PresignedUploadURLGenerationError,
    StorageObjectNotFoundError,
    StorageProxyError,
)
from ..utils import log_client_api_entry

if TYPE_CHECKING:
    from ..context import RootContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

_DEFAULT_CHUNKS = 8192  # Default chunk size for streaming uploads
_DEFAULT_TOKEN_DURATION = 1800  # Default token expiration time in seconds

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

    await log_client_api_entry(log, "stream_upload", token_data)

    try:
        ctx: RootContext = request.app["ctx"]
        # Get S3 client configuration from context
        storage_config = None
        for storage in ctx.local_config.storages:
            if storage.bucket == token_data.bucket:
                storage_config = storage
                break

        if not storage_config:
            raise web.HTTPBadRequest(
                reason=f"No storage configuration found for bucket: {token_data.bucket}"
            )

        s3_client = S3Client(
            bucket_name=token_data.bucket,
            endpoint_url=storage_config.endpoint,
            region_name=storage_config.region,
            aws_access_key_id=storage_config.access_key,
            aws_secret_access_key=storage_config.secret_key,
        )

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

        # Upload the stream
        success = await s3_client.upload_stream(
            data_stream(),
            token_data.key,
            content_type=token_data.content_type,
        )

        if success:
            response = UploadResponse(success=True, key=token_data.key)
            return web.Response(
                status=HTTPStatus.OK,
                body=dump_json_str(response.model_dump()),
                content_type="application/json",
            )
        else:
            error_response = ErrorResponse(error="Upload failed")
            return web.Response(
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
                body=dump_json_str(error_response.model_dump()),
                content_type="application/json",
            )

    except Exception as e:
        log.error(f"Stream upload failed: {e}")
        raise StorageProxyError("Upload failed") from e


async def presigned_upload_url(request: web.Request) -> web.Response:
    """Generate presigned upload URL"""
    token_data = await validate_token_request(request)
    if token_data.op != "presigned_upload":
        raise web.HTTPBadRequest(reason="Invalid token operation for presigned upload")

    await log_client_api_entry(log, "presigned_upload_url", token_data)

    try:
        ctx: RootContext = request.app["ctx"]
        storage_config = None
        for storage in ctx.local_config.storages:
            if storage.bucket == token_data.bucket:
                storage_config = storage
                break

        if not storage_config:
            raise web.HTTPBadRequest(
                reason=f"No storage configuration found for bucket: {token_data.bucket}"
            )

        s3_client = S3Client(
            bucket_name=token_data.bucket,
            endpoint_url=storage_config.endpoint,
            region_name=storage_config.region,
            aws_access_key_id=storage_config.access_key,
            aws_secret_access_key=storage_config.secret_key,
        )

        presigned_data = await s3_client.generate_presigned_upload_url(
            token_data.key,
            expiration=token_data.expiration or _DEFAULT_TOKEN_DURATION,
            content_type=token_data.content_type,
            content_length_range=(token_data.min_size, token_data.max_size)
            if token_data.min_size and token_data.max_size
            else None,
        )

        if presigned_data is None:
            raise PresignedUploadURLGenerationError()

        response = PresignedUploadResponse(url=presigned_data.url, fields=presigned_data.fields)
        return web.Response(
            status=HTTPStatus.OK,
            body=dump_json_str(response.model_dump()),
            content_type="application/json",
        )

    except Exception as e:
        log.error(f"Presigned upload URL generation failed: {e}")
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

    await log_client_api_entry(log, "presigned_download_url", token_data)

    try:
        ctx: RootContext = request.app["ctx"]
        storage_config = None
        for storage in ctx.local_config.storages:
            if storage.bucket == token_data.bucket:
                storage_config = storage
                break

        if not storage_config:
            raise web.HTTPBadRequest(
                reason=f"No storage configuration found for bucket: {token_data.bucket}"
            )

        s3_client = S3Client(
            bucket_name=token_data.bucket,
            endpoint_url=storage_config.endpoint,
            region_name=storage_config.region,
            aws_access_key_id=storage_config.access_key,
            aws_secret_access_key=storage_config.secret_key,
        )

        presigned_url = await s3_client.generate_presigned_download_url(
            token_data.key,
            expiration=token_data.expiration or _DEFAULT_TOKEN_DURATION,
        )

        if presigned_url is None:
            raise PresignedDownloadURLGenerationError()

        response = PresignedDownloadResponse(url=presigned_url)
        return web.Response(
            status=HTTPStatus.OK,
            body=dump_json_str(response.model_dump()),
            content_type="application/json",
        )

    except Exception as e:
        log.error(f"Presigned download URL generation failed: {e}")
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

    await log_client_api_entry(log, "get_object_info", token_data)

    try:
        ctx: RootContext = request.app["ctx"]
        storage_config = None
        for storage in ctx.local_config.storages:
            if storage.bucket == token_data.bucket:
                storage_config = storage
                break

        if not storage_config:
            raise web.HTTPBadRequest(
                reason=f"No storage configuration found for bucket: {token_data.bucket}"
            )

        s3_client = S3Client(
            bucket_name=token_data.bucket,
            endpoint_url=storage_config.endpoint,
            region_name=storage_config.region,
            aws_access_key_id=storage_config.access_key,
            aws_secret_access_key=storage_config.secret_key,
        )

        object_info = await s3_client.get_object_info(token_data.key)

        if object_info is None:
            raise StorageObjectNotFoundError()

        response = ObjectInfoResponse(
            content_length=object_info.content_length,
            content_type=object_info.content_type,
            last_modified=object_info.last_modified,
            etag=object_info.etag,
        )
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

    await log_client_api_entry(log, "delete_object", token_data)

    try:
        ctx: RootContext = request.app["ctx"]
        storage_config = None
        for storage in ctx.local_config.storages:
            if storage.bucket == token_data.bucket:
                storage_config = storage
                break

        if not storage_config:
            raise web.HTTPBadRequest(
                reason=f"No storage configuration found for bucket: {token_data.bucket}"
            )

        s3_client = S3Client(
            bucket_name=token_data.bucket,
            endpoint_url=storage_config.endpoint,
            region_name=storage_config.region,
            aws_access_key_id=storage_config.access_key,
            aws_secret_access_key=storage_config.secret_key,
        )

        success = await s3_client.delete_object(token_data.key)

        response = DeleteResponse(success=success)
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
