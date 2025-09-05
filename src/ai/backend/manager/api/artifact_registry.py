from __future__ import annotations

import logging
from http import HTTPStatus
from typing import Iterable, Tuple

import aiohttp_cors
from aiohttp import web

from ai.backend.common.api_handlers import APIResponse, BodyParam, api_handler
from ai.backend.common.data.storage.registries.types import ModelSortKey
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.dto.context import ProcessorsCtx
from ai.backend.manager.dto.request import (
    CleanupArtifactsReq,
    ScanArtifactModelsReq,
    ScanArtifactsReq,
    SearchArtifactsReq,
)
from ai.backend.manager.dto.response import (
    CleanupArtifactsResponse,
    ScanArtifactModelsResponse,
    SearchArtifactsResponse,
)
from ai.backend.manager.services.artifact.actions.list_with_revisions import (
    ListArtifactsWithRevisionsAction,
)
from ai.backend.manager.services.artifact.actions.retrieve_model_multi import (
    RetrieveModelsAction,
)
from ai.backend.manager.services.artifact.actions.scan import ScanArtifactsAction
from ai.backend.manager.services.artifact_revision.actions.cleanup import (
    CleanupArtifactRevisionAction,
)

from .auth import auth_required_for_method
from .types import CORSOptions, WebMiddleware

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class APIHandler:
    @auth_required_for_method
    @api_handler
    async def scan_artifacts(
        self,
        body: BodyParam[ScanArtifactsReq],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        processors = processors_ctx.processors
        await processors.artifact.scan.wait_for_complete(
            ScanArtifactsAction(
                registry_id=body.parsed.registry_id,
                artifact_type=body.parsed.artifact_type,
                limit=body.parsed.limit,
                order=ModelSortKey.DOWNLOADS,
                search=body.parsed.search,
            )
        )

        return APIResponse.no_content(status_code=HTTPStatus.OK)

    @auth_required_for_method
    @api_handler
    async def search_artifacts(
        self,
        body: BodyParam[SearchArtifactsReq],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        processors = processors_ctx.processors
        pagination = body.parsed.pagination

        action_result = await processors.artifact.list_artifacts_with_revisions.wait_for_complete(
            ListArtifactsWithRevisionsAction(
                pagination=pagination,
                ordering=None,
                filters=None,
            )
        )

        resp = SearchArtifactsResponse(
            artifacts=action_result.data,
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def scan_artifact_models(
        self,
        body: BodyParam[ScanArtifactModelsReq],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        processors = processors_ctx.processors
        action_result = await processors.artifact.retrieve_models.wait_for_complete(
            RetrieveModelsAction(
                models=body.parsed.models,
                registry_id=body.parsed.registry_id,
            )
        )

        resp = ScanArtifactModelsResponse(
            artifacts=action_result.result,
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def cleanup_artifacts(
        self,
        body: BodyParam[CleanupArtifactsReq],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        processors = processors_ctx.processors
        cleaned_revisions = []

        # Process each artifact revision sequentially
        # TODO: Optimize with asyncio.gather() for parallel processing
        for artifact_revision_id in body.parsed.artifact_revision_ids:
            action_result = await processors.artifact_revision.cleanup.wait_for_complete(
                CleanupArtifactRevisionAction(
                    artifact_revision_id=artifact_revision_id,
                )
            )
            cleaned_revisions.append(action_result.result)

        resp = CleanupArtifactsResponse(
            artifact_revisions=cleaned_revisions,
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)


def create_app(
    default_cors_options: CORSOptions,
) -> Tuple[web.Application, Iterable[WebMiddleware]]:
    app = web.Application()
    app["api_versions"] = (1, 2, 3, 4, 5)
    app["prefix"] = "artifact-registries"
    cors = aiohttp_cors.setup(app, defaults=default_cors_options)
    api_handler = APIHandler()
    cors.add(app.router.add_route("POST", "/scan", api_handler.scan_artifacts))
    cors.add(app.router.add_route("POST", "/search", api_handler.search_artifacts))
    cors.add(app.router.add_route("POST", "/scan/models", api_handler.scan_artifact_models))
    cors.add(app.router.add_route("DELETE", "/cleanup", api_handler.cleanup_artifacts))
    return app, []
