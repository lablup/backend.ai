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
from ai.backend.common.data.entity.artifact_registry import ArtifactRegistryID
from ai.backend.common.data.storage.registries.types import ModelSortKey, ModelTarget
from ai.backend.common.dto.manager.artifact_registry.request import (
    ArtifactFilterInput,
    ArtifactOrderingInput,
    DelegateeTargetInput,
    DelegateImportArtifactsRequest,
    DelegateScanArtifactsRequest,
    ScanArtifactModelPathParam,
    ScanArtifactModelQueryParam,
    ScanArtifactModelsRequest,
    ScanArtifactsRequest,
    SearchArtifactsRequest,
)
from ai.backend.common.dto.manager.artifact_registry.response import (
    ArtifactRevisionImportTaskDTO,
    ArtifactRevisionReadmeDTO,
    DelegateImportArtifactsResponse,
    DelegateScanArtifactsResponse,
    RetrieveArtifactModelResponse,
    ScanArtifactModelsResponse,
    ScanArtifactsResponse,
    SearchArtifactsResponse,
)
from ai.backend.common.dto.manager.v2.artifact import types as v2_types
from ai.backend.logging.structured import StructuredLogger
from ai.backend.manager.api.rest.artifact.converters import (
    artifact_with_revisions_and_readme_to_dto,
    artifact_with_revisions_to_dto,
    revision_to_dto,
)
from ai.backend.manager.data.artifact.types import (
    ArtifactAvailability,
    ArtifactType,
    DelegateeTarget,
)
from ai.backend.manager.data.common.types import StringFilterData
from ai.backend.manager.errors.artifact import ArtifactImportDelegationError
from ai.backend.manager.models.artifact.row import ArtifactRow
from ai.backend.manager.models.artifact.searchers import ArtifactWithRevisionsSearcher
from ai.backend.manager.models.clauses import QueryCondition, QueryOrder
from ai.backend.manager.models.specs.pagination import OffsetPagination
from ai.backend.manager.services.artifact.actions.delegate_scan import DelegateScanArtifactsAction
from ai.backend.manager.services.artifact.actions.retrieve_model import RetrieveModelAction
from ai.backend.manager.services.artifact.actions.retrieve_model_multi import (
    RetrieveModelsAction,
)
from ai.backend.manager.services.artifact.actions.scan import ScanArtifactsAction
from ai.backend.manager.services.artifact.actions.search_with_revisions import (
    SearchArtifactsWithRevisionsAction,
)
from ai.backend.manager.services.artifact.revision.actions.delegate_import_revision_batch import (
    DelegateImportArtifactRevisionBatchAction,
)

if TYPE_CHECKING:
    from ai.backend.manager.services.artifact.processors import ArtifactProcessors
    from ai.backend.manager.services.artifact.revision.processors import ArtifactRevisionProcessors

log: Final = StructuredLogger(logging.getLogger(__spec__.name))


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
        body: BodyParam[ScanArtifactsRequest],
    ) -> APIResponse:
        """
        Scan external registries to discover available artifacts.

        Searches HuggingFace or Reservoir registries for artifacts matching the specified
        criteria and registers them in the system with SCANNED status. The artifacts
        become available for import but are not downloaded until explicitly imported.

        This is the first step in the artifact workflow: Scan -> Import -> Use.
        """

        action_result = await self._artifact.scan.run(
            ScanArtifactsAction(
                registry_id=ArtifactRegistryID(body.parsed.registry_id)
                if body.parsed.registry_id is not None
                else None,
                artifact_type=_to_artifact_type(body.parsed.artifact_type),
                limit=body.parsed.limit,
                order=ModelSortKey.DOWNLOADS,
                search=body.parsed.search,
            )
        )

        resp = ScanArtifactsResponse(
            artifacts=[
                artifact_with_revisions_to_dto(artifact) for artifact in action_result.result
            ],
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    async def delegate_scan_artifacts(
        self,
        body: BodyParam[DelegateScanArtifactsRequest],
    ) -> APIResponse:
        action_result = await self._artifact.delegate_scan.run(
            DelegateScanArtifactsAction(
                delegator_reservoir_id=body.parsed.delegator_reservoir_id,
                artifact_type=_to_artifact_type(body.parsed.artifact_type),
                search=body.parsed.search,
                order=ModelSortKey.DOWNLOADS,
                delegatee_target=_to_delegatee_target(body.parsed.delegatee_target),
                limit=body.parsed.limit,
            )
        )

        resp = DelegateScanArtifactsResponse(
            artifacts=[
                artifact_with_revisions_to_dto(artifact) for artifact in action_result.result
            ],
            source_registry_id=ArtifactRegistryID(action_result.source_registry_id)
            if action_result.source_registry_id is not None
            else None,
            source_registry_type=action_result.source_registry_type,
            readme_data={
                revision_id: ArtifactRevisionReadmeDTO(readme=readme.readme)
                for revision_id, readme in action_result.readme_data.items()
            },
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    async def delegate_import_artifacts(
        self,
        body: BodyParam[DelegateImportArtifactsRequest],
    ) -> APIResponse:
        force = body.parsed.options.force
        action_result = await self._artifact_revision.delegate_import_revision_batch.run(
            DelegateImportArtifactRevisionBatchAction(
                delegator_reservoir_id=body.parsed.delegator_reservoir_id,
                artifact_type=_to_artifact_type(body.parsed.artifact_type),
                delegatee_target=_to_delegatee_target(body.parsed.delegatee_target),
                artifact_revision_ids=body.parsed.artifact_revision_ids,
                force=force,
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
                ArtifactRevisionImportTaskDTO(
                    task_id=task_id,
                    artifact_revision=revision_to_dto(revision),
                )
            )

        resp = DelegateImportArtifactsResponse(tasks=tasks)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    async def search_artifacts(
        self,
        body: BodyParam[SearchArtifactsRequest],
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

        # Build the searcher from REST pagination options
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

        action_result = await self._artifact.search_artifacts_with_revisions.run(
            SearchArtifactsWithRevisionsAction(
                searcher=ArtifactWithRevisionsSearcher(
                    pagination=pagination, conditions=conditions, orders=orders
                )
            )
        )

        artifacts = action_result.data
        resp = SearchArtifactsResponse(
            artifacts=[artifact_with_revisions_to_dto(artifact) for artifact in artifacts],
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    async def scan_models(
        self,
        body: BodyParam[ScanArtifactModelsRequest],
    ) -> APIResponse:
        """
        Perform batch scanning of specific models from external registries.

        Scans multiple specified models and retrieves detailed information.
        The README content and file sizes are processed in the background,
        unlike single model scanning which retrieves this information immediately.
        """

        action_result = await self._artifact.retrieve_models.run(
            RetrieveModelsAction(
                models=body.parsed.models,
                registry_id=ArtifactRegistryID(body.parsed.registry_id)
                if body.parsed.registry_id is not None
                else None,
            )
        )

        resp = ScanArtifactModelsResponse(
            artifacts=[
                artifact_with_revisions_to_dto(artifact) for artifact in action_result.result
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
        action_result = await self._artifact.retrieve_single_model.run(
            RetrieveModelAction(
                model=model,
                registry_id=ArtifactRegistryID(query.parsed.registry_id)
                if query.parsed.registry_id is not None
                else None,
            )
        )

        resp = RetrieveArtifactModelResponse(
            artifact=artifact_with_revisions_and_readme_to_dto(action_result.result)
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)


def _build_artifact_filter_conditions(
    filters: ArtifactFilterInput,
) -> list[QueryCondition]:
    """Convert ArtifactFilterInput to a list of QueryConditions for the searcher."""
    conditions: list[QueryCondition] = []

    if filters.artifact_type:
        artifact_types = [ArtifactType(t.value) for t in filters.artifact_type]
        conditions.append(lambda: ArtifactRow.type.in_(artifact_types))

    if filters.name_filter is not None:
        name_filter = StringFilterData(
            **filters.name_filter.model_dump(include=set(_STRING_FILTER_FIELDS))
        )

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
        availability = [ArtifactAvailability(a.value) for a in filters.availability]
        conditions.append(lambda: ArtifactRow.availability.in_(availability))

    return conditions


def _build_artifact_query_orders(
    ordering: ArtifactOrderingInput,
) -> list[QueryOrder]:
    """Convert ArtifactOrderingInput to a list of QueryOrders for the searcher."""
    orders: list[QueryOrder] = []
    for field, desc in ordering.order_by:
        column: Any = getattr(ArtifactRow, field.value.lower(), ArtifactRow.name)
        if desc:
            orders.append(column.desc())
        else:
            orders.append(column.asc())
    return orders


_STRING_FILTER_FIELDS: Final = (
    "contains",
    "starts_with",
    "ends_with",
    "equals",
    "not_equals",
    "i_contains",
    "i_starts_with",
    "i_ends_with",
    "i_equals",
    "i_not_equals",
)


def _to_artifact_type(value: v2_types.ArtifactType | None) -> ArtifactType | None:
    return ArtifactType(value.value) if value is not None else None


def _to_delegatee_target(value: DelegateeTargetInput | None) -> DelegateeTarget | None:
    if value is None:
        return None
    return DelegateeTarget(
        delegatee_reservoir_id=value.delegatee_reservoir_id,
        target_registry_id=value.target_registry_id,
    )
