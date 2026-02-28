"""Artifact registry handler class using constructor dependency injection.

All handlers use the new ApiHandler pattern: typed parameters
(``BodyParam``, ``PathParam``, ``QueryParam``) are automatically
extracted by ``_wrap_api_handler`` and responses are returned as
``APIResponse`` objects.
"""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from ai.backend.common.api_handlers import APIResponse, BodyParam, PathParam, QueryParam
from ai.backend.common.data.storage.registries.types import ModelSortKey, ModelTarget
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.artifact.types import (
    ArtifactDataWithRevisionsResponse,
    ArtifactRevisionResponseData,
)
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

if TYPE_CHECKING:
    from ai.backend.manager.services.processors import Processors

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ArtifactRegistryHandler:
    """Artifact registry API handler with constructor-injected dependencies."""

    def __init__(self, *, processors: Processors | None = None) -> None:
        self._processors_ref = processors

    def bind_processors(self, processors: Processors) -> None:
        """Late-bind processors for backward-compatible create_app() usage."""
        self._processors_ref = processors

    @property
    def _processors(self) -> Processors:
        if self._processors_ref is None:
            raise RuntimeError(
                "Processors not bound. Pass processors= to __init__ or call bind_processors()."
            )
        return self._processors_ref

    async def scan_artifacts(
        self,
        body: BodyParam[ScanArtifactsReq],
    ) -> APIResponse:
        """
        Scan external registries to discover available artifacts.

        Searches HuggingFace or Reservoir registries for artifacts matching the specified
        criteria and registers them in the system with SCANNED status. The artifacts
        become available for import but are not downloaded until explicitly imported.

        This is the first step in the artifact workflow: Scan -> Import -> Use.
        """
        processors = self._processors
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

    async def delegate_scan_artifacts(
        self,
        body: BodyParam[DelegateScanArtifactsReq],
    ) -> APIResponse:
        processors = self._processors
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

    async def delegate_import_artifacts(
        self,
        body: BodyParam[DelegateImportArtifactsReq],
    ) -> APIResponse:
        processors = self._processors
        force = body.parsed.options.force
        action_result = (
            await processors.artifact_revision.delegate_import_revision_batch.wait_for_complete(
                DelegateImportArtifactRevisionBatchAction(
                    delegator_reservoir_id=body.parsed.delegator_reservoir_id,
                    artifact_type=body.parsed.artifact_type,
                    delegatee_target=body.parsed.delegatee_target
                    if body.parsed.delegatee_target
                    else None,
                    artifact_revision_ids=body.parsed.artifact_revision_ids,
                    force=force,
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

    async def search_artifacts(
        self,
        body: BodyParam[SearchArtifactsReq],
    ) -> APIResponse:
        """
        Search registered artifacts with cursor-based pagination.

        Returns artifacts that have been previously scanned and registered in the system.
        Supports efficient pagination for browsing through large datasets of artifacts
        with their revision information.
        """
        processors = self._processors
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

    async def scan_models(
        self,
        body: BodyParam[ScanArtifactModelsReq],
    ) -> APIResponse:
        """
        Perform batch scanning of specific models from external registries.

        Scans multiple specified models and retrieves detailed information.
        The README content and file sizes are processed in the background,
        unlike single model scanning which retrieves this information immediately.
        """
        processors = self._processors
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

    async def scan_single_model(
        self,
        path: PathParam[ScanArtifactModelPathParam],
        query: QueryParam[ScanArtifactModelQueryParam],
    ) -> APIResponse:
        """
        Scan a single model and retrieve detailed information immediately.

        Performs immediate detailed scanning of a specified model including
        README content and file sizes. This provides complete metadata
        for the model, ready for import or direct use.
        """
        processors = self._processors
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
