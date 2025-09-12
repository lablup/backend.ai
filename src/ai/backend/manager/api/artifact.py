from __future__ import annotations

import logging
from http import HTTPStatus
from typing import Iterable, Tuple

import aiohttp_cors
from aiohttp import web

from ai.backend.common.api_handlers import APIResponse, BodyParam, PathParam, api_handler
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.artifact.types import ArtifactRevisionResponseData
from ai.backend.manager.dto.context import ProcessorsCtx
from ai.backend.manager.dto.request import (
    ApproveArtifactRevisionReq,
    CancelImportArtifactReq,
    CleanupArtifactsReq,
    GetArtifactRevisionReadmeReq,
    ImportArtifactsReq,
    RejectArtifactRevisionReq,
    UpdateArtifactReqBodyParam,
    UpdateArtifactReqPathParam,
)
from ai.backend.manager.dto.response import (
    ApproveArtifactRevisionResponse,
    ArtifactRevisionImportTask,
    CancelImportArtifactResponse,
    CleanupArtifactsResponse,
    GetArtifactRevisionReadmeResponse,
    ImportArtifactsResponse,
    RejectArtifactRevisionResponse,
    UpdateArtifactResponse,
)
from ai.backend.manager.services.artifact.actions.update import UpdateArtifactAction
from ai.backend.manager.services.artifact_revision.actions.approve import (
    ApproveArtifactRevisionAction,
)
from ai.backend.manager.services.artifact_revision.actions.cancel_import import (
    CancelImportAction,
)
from ai.backend.manager.services.artifact_revision.actions.cleanup import (
    CleanupArtifactRevisionAction,
)
from ai.backend.manager.services.artifact_revision.actions.get_readme import (
    GetArtifactRevisionReadmeAction,
)
from ai.backend.manager.services.artifact_revision.actions.import_revision import (
    ImportArtifactRevisionAction,
)
from ai.backend.manager.services.artifact_revision.actions.reject import (
    RejectArtifactRevisionAction,
)

from .auth import auth_required_for_method
from .types import CORSOptions, WebMiddleware

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class APIHandler:
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
            artifact_revisions=[
                ArtifactRevisionResponseData.from_revision_data(revision)
                for revision in cleaned_revisions
            ],
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def cancel_import_artifact(
        self,
        body: BodyParam[CancelImportArtifactReq],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        processors = processors_ctx.processors
        action_result = await processors.artifact_revision.cancel_import.wait_for_complete(
            CancelImportAction(
                artifact_revision_id=body.parsed.artifact_revision_id,
            )
        )

        resp = CancelImportArtifactResponse(
            artifact_revision=ArtifactRevisionResponseData.from_revision_data(action_result.result),
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def approve_artifact_revision(
        self,
        path: PathParam[ApproveArtifactRevisionReq],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        processors = processors_ctx.processors
        action_result = await processors.artifact_revision.approve.wait_for_complete(
            ApproveArtifactRevisionAction(
                artifact_revision_id=path.parsed.artifact_revision_id,
            )
        )

        resp = ApproveArtifactRevisionResponse(
            artifact_revision=ArtifactRevisionResponseData.from_revision_data(action_result.result),
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def reject_artifact_revision(
        self,
        path: PathParam[RejectArtifactRevisionReq],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        processors = processors_ctx.processors
        action_result = await processors.artifact_revision.reject.wait_for_complete(
            RejectArtifactRevisionAction(
                artifact_revision_id=path.parsed.artifact_revision_id,
            )
        )

        resp = RejectArtifactRevisionResponse(
            artifact_revision=ArtifactRevisionResponseData.from_revision_data(action_result.result),
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def import_artifacts(
        self,
        body: BodyParam[ImportArtifactsReq],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        processors = processors_ctx.processors
        imported_revisions = []
        tasks = []

        # Process each artifact revision sequentially
        # TODO: Optimize with asyncio.gather() for parallel processing
        for artifact_revision_id in body.parsed.artifact_revision_ids:
            action_result = await processors.artifact_revision.import_revision.wait_for_complete(
                ImportArtifactRevisionAction(
                    artifact_revision_id=artifact_revision_id,
                )
            )
            imported_revisions.append(action_result.result)
            tasks.append(
                ArtifactRevisionImportTask(
                    task_id=str(action_result.task_id),
                    artifact_revision=ArtifactRevisionResponseData.from_revision_data(
                        action_result.result
                    ),
                )
            )

        resp = ImportArtifactsResponse(tasks=tasks)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def update_artifact(
        self,
        path: PathParam[UpdateArtifactReqPathParam],
        body: BodyParam[UpdateArtifactReqBodyParam],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        processors = processors_ctx.processors
        action_result = await processors.artifact.update.wait_for_complete(
            UpdateArtifactAction(
                artifact_id=path.parsed.artifact_id,
                modifier=body.parsed.to_modifier(),
            )
        )

        resp = UpdateArtifactResponse(
            artifact=action_result.result,
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def get_artifact_revision_readme(
        self,
        path: PathParam[GetArtifactRevisionReadmeReq],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        processors = processors_ctx.processors
        action_result = await processors.artifact_revision.get_readme.wait_for_complete(
            GetArtifactRevisionReadmeAction(
                artifact_revision_id=path.parsed.artifact_revision_id,
            )
        )

        resp = GetArtifactRevisionReadmeResponse(
            readme=action_result.readme_data.readme,
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)


def create_app(
    default_cors_options: CORSOptions,
) -> Tuple[web.Application, Iterable[WebMiddleware]]:
    app = web.Application()
    app["api_versions"] = (1, 2, 3, 4, 5)
    app["prefix"] = "artifacts"
    cors = aiohttp_cors.setup(app, defaults=default_cors_options)
    api_handler = APIHandler()

    cors.add(app.router.add_route("POST", "/revisions/cleanup", api_handler.cleanup_artifacts))
    cors.add(
        app.router.add_route(
            "POST",
            "/revisions/{artifact_revision_id}/approval",
            api_handler.approve_artifact_revision,
        )
    )
    cors.add(
        app.router.add_route(
            "POST",
            "/revisions/{artifact_revision_id}/rejection",
            api_handler.reject_artifact_revision,
        )
    )
    cors.add(app.router.add_route("POST", "/task/cancel", api_handler.cancel_import_artifact))
    cors.add(app.router.add_route("POST", "/import", api_handler.import_artifacts))
    cors.add(app.router.add_route("PATCH", "/{artifact_id}", api_handler.update_artifact))
    cors.add(
        app.router.add_route(
            "GET",
            "/revisions/{artifact_revision_id}/readme",
            api_handler.get_artifact_revision_readme,
        )
    )

    return app, []
