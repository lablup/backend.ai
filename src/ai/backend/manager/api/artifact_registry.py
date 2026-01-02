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
    ArtifactRevisionResponseData,
)
from ai.backend.manager.dto.context import ProcessorsCtx
from ai.backend.manager.dto.request import (
    DelegateImportArtifactsReq,
    DelegateScanArtifactsReq,
    ScanArtifactModelPathParam,
    ScanArtifactModelQueryParam,
    ScanArtifactModelsReq,
    ScanArtifactsReq,
    SearchArtifactsReq,
)
from ai.backend.manager.dto.response import (
    ArtifactRevisionImportTask,
    DelegateImportArtifactsResponse,
    DelegateScanArtifactsResponse,
    RetreiveArtifactModelResponse,
    ScanArtifactModelsResponse,
    ScanArtifactsResponse,
    SearchArtifactsResponse,
)
from ai.backend.manager.errors.artifact import ArtifactImportDelegationError
from ai.backend.manager.services.artifact.actions.delegate_scan import DelegateScanArtifactsAction
from ai.backend.manager.services.artifact.actions.list_with_revisions import (
    ListArtifactsWithRevisionsAction,
)
from ai.backend.manager.services.artifact.actions.retrieve_model import RetrieveModelAction
from ai.backend.manager.services.artifact.actions.retrieve_model_multi import (
    RetrieveModelsAction,
)
from ai.backend.manager.services.artifact.actions.scan import ScanArtifactsAction
from ai.backend.manager.services.artifact_revision.actions.delegate_import_revision_batch import (
    DelegateImportArtifactRevisionBatchAction,
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
    async def delegate_scan_artifacts(
        self,
        body: BodyParam[DelegateScanArtifactsReq],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        processors = processors_ctx.processors
        action_result = await processors.artifact.delegate_scan.wait_for_complete(
            DelegateScanArtifactsAction(
                delegator_reservoir_id=body.parsed.delegator_reservoir_id,
                artifact_type=body.parsed.artifact_type,
                search=body.parsed.search,
                order=ModelSortKey.DOWNLOADS,
                delegatee_target=body.parsed.delegatee_target
                if body.parsed.delegatee_target
                else None,
                limit=body.parsed.limit,
            )
        )

        resp = DelegateScanArtifactsResponse(
            artifacts=[
                ArtifactDataWithRevisionsResponse.from_artifact_with_revisions(artifact)
                for artifact in action_result.result
            ],
            source_registry_id=action_result.source_registry_id,
            source_registry_type=action_result.source_registry_type,
            readme_data=action_result.readme_data,
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def delegate_import_artifacts(
        self,
        body: BodyParam[DelegateImportArtifactsReq],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        processors = processors_ctx.processors
        action_result = (
            await processors.artifact_revision.delegate_import_revision_batch.wait_for_complete(
                DelegateImportArtifactRevisionBatchAction(
                    delegator_reservoir_id=body.parsed.delegator_reservoir_id,
                    artifact_type=body.parsed.artifact_type,
                    delegatee_target=body.parsed.delegatee_target
                    if body.parsed.delegatee_target
                    else None,
                    artifact_revision_ids=body.parsed.artifact_revision_ids,
                )
            )
        )

        if len(action_result.result) != len(action_result.task_ids):
            raise ArtifactImportDelegationError(
                "Mismatch between artifact revisions and task IDs returned"
            )

        # Convert to ArtifactRevisionImportTask format
        tasks = []
        for task_uuid, revision in zip(action_result.task_ids, action_result.result, strict=True):
            task_id = str(task_uuid) if task_uuid is not None else None
            tasks.append(
                ArtifactRevisionImportTask(
                    task_id=task_id,
                    artifact_revision=ArtifactRevisionResponseData.from_revision_data(revision),
                )
            )

        resp = DelegateImportArtifactsResponse(tasks=tasks)
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
        filters = body.parsed.filters
        ordering = body.parsed.ordering

        action_result = await processors.artifact.list_artifacts_with_revisions.wait_for_complete(
            ListArtifactsWithRevisionsAction(
                pagination=pagination,
                ordering=ordering,
                filters=filters,
            )
        )

        artifacts = action_result.data
        resp = SearchArtifactsResponse(
            artifacts=[
                ArtifactDataWithRevisionsResponse.from_artifact_with_revisions(artifact)
                for artifact in artifacts
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
    cors.add(app.router.add_route("POST", "/delegation/scan", api_handler.delegate_scan_artifacts))
    cors.add(
        app.router.add_route("POST", "/delegation/import", api_handler.delegate_import_artifacts)
    )
    cors.add(app.router.add_route("POST", "/search", api_handler.search_artifacts))

    cors.add(app.router.add_route("GET", "/model/{model_id}", api_handler.scan_single_model))
    cors.add(app.router.add_route("POST", "/models/batch", api_handler.scan_models))
    return app, []
