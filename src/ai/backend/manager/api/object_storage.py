from __future__ import annotations

import json
import logging
import uuid
from http import HTTPStatus
from typing import Iterable, Tuple

import aiohttp_cors
from aiohttp import web

from ai.backend.common.api_handlers import APIResponse, BodyParam, PathParam, api_handler
from ai.backend.common.dto.manager.request import (
    GetPresignedDownloadURLReq,
    GetPresignedUploadURLReq,
    ObjectStoragePathParam,
)
from ai.backend.common.dto.manager.response import (
    GetPresignedDownloadURLResponse,
    GetPresignedUploadURLResponse,
    ObjectStorageAllBucketsResponse,
    ObjectStorageBucketsResponse,
    ObjectStorageListResponse,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.dto.context import ProcessorsCtx
from ai.backend.manager.services.object_storage.actions.get_download_presigned_url import (
    GetDownloadPresignedURLAction,
)
from ai.backend.manager.services.object_storage.actions.get_upload_presigned_url import (
    GetUploadPresignedURLAction,
)
from ai.backend.manager.services.object_storage.actions.list import (
    ListObjectStorageAction,
)
from ai.backend.manager.services.storage_namespace.actions.get_all import GetAllNamespacesAction
from ai.backend.manager.services.storage_namespace.actions.get_multi import GetNamespacesAction

from .auth import auth_required_for_method
from .types import CORSOptions, WebMiddleware

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class APIHandler:
    @auth_required_for_method
    @api_handler
    async def get_presigned_download_url(
        self,
        body: BodyParam[GetPresignedDownloadURLReq],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        processors = processors_ctx.processors

        action_result = (
            await processors.object_storage.get_presigned_download_url.wait_for_complete(
                GetDownloadPresignedURLAction(
                    artifact_revision_id=body.parsed.artifact_revision_id,
                    key=body.parsed.key,
                    expiration=body.parsed.expiration,
                )
            )
        )

        resp = GetPresignedDownloadURLResponse(presigned_url=action_result.presigned_url)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def get_presigned_upload_url(
        self,
        body: BodyParam[GetPresignedUploadURLReq],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        processors = processors_ctx.processors

        action_result = await processors.object_storage.get_presigned_upload_url.wait_for_complete(
            GetUploadPresignedURLAction(
                artifact_revision_id=body.parsed.artifact_revision_id,
                key=body.parsed.key,
            )
        )

        resp = GetPresignedUploadURLResponse(
            presigned_url=action_result.presigned_url,
            fields=json.dumps(action_result.fields),
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def get_all_buckets(
        self,
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        processors = processors_ctx.processors
        action_result = await processors.storage_namespace.get_all_namespaces.wait_for_complete(
            GetAllNamespacesAction()
        )

        resp = ObjectStorageAllBucketsResponse(buckets_by_storage=action_result.result)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def get_buckets(
        self,
        path: PathParam[ObjectStoragePathParam],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        processors = processors_ctx.processors
        storage_id: uuid.UUID = path.parsed.storage_id

        action_result = await processors.storage_namespace.get_namespaces.wait_for_complete(
            GetNamespacesAction(storage_id=storage_id)
        )

        bucket_names = [namespace_data.namespace for namespace_data in action_result.result]
        resp = ObjectStorageBucketsResponse(buckets=bucket_names)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def list_object_storages(
        self,
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        processors = processors_ctx.processors

        action_result = await processors.object_storage.list_storages.wait_for_complete(
            ListObjectStorageAction()
        )

        # Convert ObjectStorageData to ObjectStorageResponse DTOs
        storage_responses = [storage_data.to_dto() for storage_data in action_result.data]

        resp = ObjectStorageListResponse(storages=storage_responses)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)


def create_app(
    default_cors_options: CORSOptions,
) -> Tuple[web.Application, Iterable[WebMiddleware]]:
    app = web.Application()
    app["api_versions"] = (1, 2, 3, 4, 5)
    app["prefix"] = "object-storages"
    cors = aiohttp_cors.setup(app, defaults=default_cors_options)
    api_handler = APIHandler()

    cors.add(
        app.router.add_route("POST", "/presigned/upload", api_handler.get_presigned_upload_url)
    )
    cors.add(
        app.router.add_route("POST", "/presigned/download", api_handler.get_presigned_download_url)
    )
    # TODO: deprecate these APIs, and use /storage-namespaces instead
    cors.add(app.router.add_route("GET", "/buckets", api_handler.get_all_buckets))
    cors.add(app.router.add_route("GET", "/{storage_id}/buckets", api_handler.get_buckets))
    cors.add(app.router.add_route("GET", "/", api_handler.list_object_storages))

    return app, []
