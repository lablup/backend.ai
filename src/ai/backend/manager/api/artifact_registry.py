from __future__ import annotations

import logging
from http import HTTPStatus
from typing import Iterable, Tuple

import aiohttp_cors
from aiohttp import web

from ai.backend.common.api_handlers import (
    APIResponse,
    BodyParam,
    PathParam,
    QueryParam,
    api_handler,
)
from ai.backend.common.data.storage.registries.types import ModelSortKey, ModelTarget
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.artifact.types import (
    ArtifactDataWithRevisionsResponse,
)
from ai.backend.manager.dto.context import ProcessorsCtx
from ai.backend.manager.dto.request import (
    ScanArtifactModelPathParam,
    ScanArtifactModelQueryParam,
    ScanArtifactModelsReq,
    ScanArtifactsReq,
    SearchArtifactsReq,
)
from ai.backend.manager.dto.response import (
    RetreiveArtifactModelResponse,
    ScanArtifactModelsResponse,
    ScanArtifactsResponse,
    SearchArtifactsResponse,
)
from ai.backend.manager.services.artifact.actions.list_with_revisions import (
    ListArtifactsWithRevisionsAction,
)
from ai.backend.manager.services.artifact.actions.retrieve_model import RetrieveModelAction
from ai.backend.manager.services.artifact.actions.retrieve_model_multi import (
    RetrieveModelsAction,
)
from ai.backend.manager.services.artifact.actions.scan import ScanArtifactsAction

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
        """
        Scan external registries to discover available artifacts.

        Searches HuggingFace or Reservoir registries for artifacts matching the specified
        criteria and registers them in the system with SCANNED status. The artifacts
        become available for import but are not downloaded until explicitly imported.

        This is the first step in the artifact workflow: Scan → Import → Use.
        """
        processors = processors_ctx.processors
        action_result = await processors.artifact.scan.wait_for_complete(
            ScanArtifactsAction(
                registry_id=body.parsed.registry_id,
                artifact_type=body.parsed.artifact_type,
                limit=body.parsed.limit,
                order=ModelSortKey.DOWNLOADS,
                search=body.parsed.search,
            )
        )

        resp = ScanArtifactsResponse(
            artifacts=[
                ArtifactDataWithRevisionsResponse.from_artifact_with_revisions(artifact)
                for artifact in action_result.result
            ],
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def search_artifacts(
        self,
        body: BodyParam[SearchArtifactsReq],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """
        Search registered artifacts with cursor-based pagination.

        Returns artifacts that have been previously scanned and registered in the system.
        Supports efficient pagination for browsing through large datasets of artifacts
        with their revision information.
        """
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
            artifacts=[
                ArtifactDataWithRevisionsResponse.from_artifact_with_revisions(artifact)
                for artifact in action_result.data
            ],
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def scan_models(
        self,
        body: BodyParam[ScanArtifactModelsReq],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """
        Perform batch scanning of specific models from external registries.

        Scans multiple specified models and retrieves detailed information.
        The README content and file sizes are processed in the background,
        unlike single model scanning which retrieves this information immediately.
        """
        processors = processors_ctx.processors
        action_result = await processors.artifact.retrieve_models.wait_for_complete(
            RetrieveModelsAction(
                models=body.parsed.models,
                registry_id=body.parsed.registry_id,
            )
        )

        resp = ScanArtifactModelsResponse(
            artifacts=[
                ArtifactDataWithRevisionsResponse.from_artifact_with_revisions(artifact)
                for artifact in action_result.result
            ],
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def scan_single_model(
        self,
        path: PathParam[ScanArtifactModelPathParam],
        query: QueryParam[ScanArtifactModelQueryParam],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """
        Scan a single model and retrieve detailed information immediately.

        Performs immediate detailed scanning of a specified model including
        README content and file sizes. This provides complete metadata
        for the model, ready for import or direct use.
        """
        processors = processors_ctx.processors
        model = ModelTarget(
            model_id=path.parsed.model_id,
            revision=query.parsed.revision,
        )
        action_result = await processors.artifact.retrieve_single_model.wait_for_complete(
            RetrieveModelAction(
                model=model,
                registry_id=query.parsed.registry_id,
            )
        )

        resp = RetreiveArtifactModelResponse(artifact=action_result.result)
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

    cors.add(app.router.add_route("GET", "/model/{model_id}", api_handler.scan_single_model))
    cors.add(app.router.add_route("POST", "/models/batch", api_handler.scan_models))
    return app, []
