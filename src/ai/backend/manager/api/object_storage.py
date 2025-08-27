from __future__ import annotations

import json
import logging
from http import HTTPStatus
from typing import Iterable, Tuple

import aiohttp_cors
from aiohttp import web

from ai.backend.common.api_handlers import APIResponse, BodyParam, api_handler
from ai.backend.common.dto.manager.request import (
    GetPresignedDownloadURLReq,
    GetPresignedUploadURLReq,
)
from ai.backend.common.dto.manager.response import (
    GetPresignedDownloadURLResponse,
    GetPresignedUploadURLResponse,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.dto.context import ProcessorsCtx
from ai.backend.manager.services.object_storage.actions.get_download_presigned_url import (
    GetDownloadPresignedURLAction,
)
from ai.backend.manager.services.object_storage.actions.get_upload_presigned_url import (
    GetUploadPresignedURLAction,
)

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
                    storage_id=body.parsed.storage_id,
                    bucket_name=body.parsed.bucket_name,
                    key=body.parsed.key,
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
                bucket_name=body.parsed.bucket_name,
                key=body.parsed.key,
                content_type=body.parsed.content_type,
                expiration=body.parsed.expiration,
                min_size=body.parsed.min_size,
                max_size=body.parsed.max_size,
            )
        )

        resp = GetPresignedUploadURLResponse(
            presigned_url=action_result.presigned_url,
            fields=json.dumps(action_result.fields),
        )
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
        app.router.add_route("GET", "/presigned/download", api_handler.get_presigned_download_url)
    )

    return app, []
