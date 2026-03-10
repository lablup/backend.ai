"""Artifact registry handler class using constructor dependency injection.

All handlers use the new ApiHandler pattern: typed parameters
(``BodyParam``, ``PathParam``, ``QueryParam``) are automatically
extracted by ``_wrap_api_handler`` and responses are returned as
``APIResponse`` objects.
"""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING, Any, Final, cast

import sqlalchemy as sa

from ai.backend.common.api_handlers import APIResponse, BodyParam, PathParam, QueryParam
from ai.backend.common.data.storage.registries.types import ModelSortKey, ModelTarget
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.artifact.types import (
    ArtifactDataWithRevisionsResponse,
    ArtifactFilterOptions,
    ArtifactOrderingOptions,
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
from ai.backend.manager.models.artifact import ArtifactRow
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    OffsetPagination,
    QueryCondition,
    QueryOrder,
)
from ai.backend.manager.services.artifact.actions.delegate_scan import DelegateScanArtifactsAction
from ai.backend.manager.services.artifact.actions.retrieve_model import RetrieveModelAction
from ai.backend.manager.services.artifact.actions.retrieve_model_multi import (
    RetrieveModelsAction,
)
from ai.backend.manager.services.artifact.actions.scan import ScanArtifactsAction
from ai.backend.manager.services.artifact.actions.search_with_revisions import (
    SearchArtifactsWithRevisionsAction,
)
from ai.backend.manager.services.artifact_revision.actions.delegate_import_revision_batch import (
    DelegateImportArtifactRevisionBatchAction,
)

if TYPE_CHECKING:
    from ai.backend.manager.services.artifact.processors import ArtifactProcessors
    from ai.backend.manager.services.artifact_revision.processors import ArtifactRevisionProcessors

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ArtifactRegistryHandler:
    """Artifact registry API handler with constructor-injected dependencies."""

    def __init__(
        self,
        *,
        artifact: ArtifactProcessors,
        artifact_revision: ArtifactRevisionProcessors,
    ) -> None:
        self._artifact = artifact
        self._artifact_revision = artifact_revision

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

        action_result = await self._artifact.scan.wait_for_complete(
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
        action_result = await self._artifact.delegate_scan.wait_for_complete(
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
        force = body.parsed.options.force
        action_result = (
            await self._artifact_revision.delegate_import_revision_batch.wait_for_complete(
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
        Search registered artifacts with offset-based pagination.

        Returns artifacts that have been previously scanned and registered in the system.
        Supports efficient pagination for browsing through large datasets of artifacts
        with their revision information.
        """

        pagination_opts = body.parsed.pagination
        filters = body.parsed.filters
        ordering = body.parsed.ordering

        # Build BatchQuerier from REST pagination options
        offset_opts = pagination_opts.offset
        pagination = OffsetPagination(
            limit=offset_opts.limit if offset_opts and offset_opts.limit is not None else 20,
            offset=offset_opts.offset if offset_opts and offset_opts.offset is not None else 0,
        )

        # Convert filter options to query conditions
        conditions: list[QueryCondition] = []
        if filters is not None:
            conditions.extend(_build_artifact_filter_conditions(filters))

        # Convert ordering options to query orders
        orders: list[QueryOrder] = []
        if ordering is not None:
            orders.extend(_build_artifact_query_orders(ordering))

        querier = BatchQuerier(
            pagination=pagination,
            conditions=conditions,
            orders=orders,
        )

        action_result = await self._artifact.search_artifacts_with_revisions.wait_for_complete(
            SearchArtifactsWithRevisionsAction(querier=querier)
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

        action_result = await self._artifact.retrieve_models.wait_for_complete(
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

        model = ModelTarget(
            model_id=path.parsed.model_id,
            revision=query.parsed.revision,
        )
        action_result = await self._artifact.retrieve_single_model.wait_for_complete(
            RetrieveModelAction(
                model=model,
                registry_id=query.parsed.registry_id,
            )
        )

        resp = RetreiveArtifactModelResponse(artifact=action_result.result)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)


def _build_artifact_filter_conditions(
    filters: ArtifactFilterOptions,
) -> list[QueryCondition]:
    """Convert ArtifactFilterOptions to a list of QueryConditions for BatchQuerier."""
    conditions: list[QueryCondition] = []

    if filters.artifact_type:
        artifact_types = filters.artifact_type
        conditions.append(lambda: ArtifactRow.type.in_(artifact_types))

    if filters.name_filter is not None:
        name_filter = filters.name_filter

        def _name_cond() -> sa.sql.expression.ColumnElement[bool]:
            cond = name_filter.apply_to_column(
                cast(sa.sql.elements.ColumnElement[str], ArtifactRow.name)
            )
            if cond is None:
                return sa.literal(True)
            return cond

        conditions.append(_name_cond)

    if filters.registry_id is not None:
        registry_id = filters.registry_id
        conditions.append(lambda: ArtifactRow.registry_id == registry_id)

    if filters.registry_type is not None:
        registry_type = filters.registry_type
        conditions.append(lambda: ArtifactRow.registry_type == registry_type)

    if filters.source_registry_id is not None:
        source_registry_id = filters.source_registry_id
        conditions.append(lambda: ArtifactRow.source_registry_id == source_registry_id)

    if filters.source_registry_type is not None:
        source_registry_type = filters.source_registry_type
        conditions.append(lambda: ArtifactRow.source_registry_type == source_registry_type)

    if filters.availability:
        availability = filters.availability
        conditions.append(lambda: ArtifactRow.availability.in_(availability))

    return conditions


def _build_artifact_query_orders(
    ordering: ArtifactOrderingOptions,
) -> list[QueryOrder]:
    """Convert ArtifactOrderingOptions to a list of QueryOrders for BatchQuerier."""
    orders: list[QueryOrder] = []
    for field, desc in ordering.order_by:
        column: Any = getattr(ArtifactRow, field.value.lower(), ArtifactRow.name)
        if desc:
            orders.append(column.desc())
        else:
            orders.append(column.asc())
    return orders
