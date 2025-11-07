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
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.artifact.types import ArtifactRevisionResponseData
from ai.backend.manager.dto.context import ProcessorsCtx, ValkeyArtifactCtx
from ai.backend.manager.dto.request import (
    ApproveArtifactRevisionReq,
    CancelImportArtifactReq,
    CleanupArtifactsReq,
    GetArtifactDownloadProgressReq,
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
    GetArtifactDownloadProgressResponse,
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
        """
        Clean up stored artifact revision data to free storage space.

        Removes the downloaded files for the specified artifact revisions and
        transitions them back to SCANNED status. The metadata remains, allowing
        the artifacts to be re-imported later if needed.

        Use this operation to manage storage usage by removing unused artifacts.
        """
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
        """
        Cancel an in-progress artifact import operation.

        Stops the download process for the specified artifact revision and
        reverts its status back to SCANNED. The partially downloaded data is cleaned up.
        """
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
        """
        Approve an artifact revision for general use.

        Admin-only operation to approve artifact revisions, typically used
        in environments with approval workflows for artifact deployment.
        """
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
        """
        Reject an artifact revision, preventing its use.

        Admin-only operation to reject artifact revisions, typically used
        in environments with approval workflows for artifact deployment.
        """
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
        """
        Import scanned artifact revisions from external registries.

        Downloads the actual files for the specified artifact revisions, transitioning
        them from SCANNED → PULLING → PULLED → AVAILABLE status.

        Returns background tasks that can be monitored for import progress.
        Once AVAILABLE, artifacts can be used by users in their sessions.
        """
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
        """
        Update artifact metadata properties.

        Modifies artifact metadata such as readonly status and description.
        This operation does not affect the actual artifact files or revisions.
        """
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
        """
        Retrieve the README content for a specific artifact revision.

        Returns the README documentation associated with the artifact revision,
        which typically contains usage instructions and model information.
        """
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

    @auth_required_for_method
    @api_handler
    async def get_download_progress(
        self,
        query: QueryParam[GetArtifactDownloadProgressReq],
        valkey_ctx: ValkeyArtifactCtx,
    ) -> APIResponse:
        """
        Query the current download progress for an artifact.

        Returns the current state of the download including artifact-level progress
        (total bytes, completed files) and per-file progress information.
        The data is retrieved from Redis where it's tracked during the download process.
        """
        valkey_artifact = valkey_ctx.valkey_artifact
        artifact_progress = await valkey_artifact.get_artifact_progress(
            model_id=query.parsed.model_id,
            revision=query.parsed.revision,
        )
        file_progress = await valkey_artifact.get_all_file_progress(
            model_id=query.parsed.model_id,
            revision=query.parsed.revision,
        )

        resp = GetArtifactDownloadProgressResponse(
            artifact_progress=artifact_progress,
            file_progress=file_progress if file_progress else None,
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
    cors.add(
        app.router.add_route(
            "GET",
            "/revisions/download-progress",
            api_handler.get_download_progress,
        )
    )

    return app, []
