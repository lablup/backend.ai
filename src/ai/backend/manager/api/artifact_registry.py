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
    ArtifactRegistriesScanReq,
    ArtifactRegistriesSearchReq,
)
from ai.backend.manager.dto.response import (
    ArtifactRegistriesScanResponse,
    ArtifactRegistriesSearchResponse,
)
from ai.backend.manager.services.artifact.actions.list_with_revisions import (
    ListArtifactsWithRevisionsAction,
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
        body: BodyParam[ArtifactRegistriesScanReq],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        processors = processors_ctx.processors
        await processors.artifact.scan.wait_for_complete(
            ScanArtifactsAction(
                registry_id=body.parsed.registry_id,
                storage_id=body.parsed.storage_id,
                limit=body.parsed.limit,
                order=ModelSortKey.DOWNLOADS,
                search=body.parsed.search,
            )
        )

        resp = ArtifactRegistriesScanResponse()
        return APIResponse.build(status_code=200, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def search_artifacts(
        self,
        body: BodyParam[ArtifactRegistriesSearchReq],
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

        resp = ArtifactRegistriesSearchResponse(
            artifacts=action_result.data,
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
    return app, []
