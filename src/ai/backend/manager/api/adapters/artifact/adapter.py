"""Artifact adapter bridging DTOs and Processors."""

from __future__ import annotations

from collections.abc import Sequence
from functools import lru_cache
from typing import assert_never
from uuid import UUID

from ai.backend.common.data.entity.artifact import ArtifactID
from ai.backend.common.data.entity.artifact_registry import ArtifactRegistryID
from ai.backend.common.data.entity.artifact_revision import ArtifactRevisionID
from ai.backend.common.data.storage.registries.types import ModelSortKey
from ai.backend.common.data.storage.registries.types import ModelTarget as StorageModelTarget
from ai.backend.common.dto.manager.v2.artifact.request import (
    AdminSearchArtifactRevisionsInput,
    AdminSearchArtifactsGQLInput,
    AdminSearchArtifactsInput,
    ArtifactFilter,
    ArtifactGQLFilterInputDTO,
    ArtifactGQLOrderByInputDTO,
    ArtifactOrder,
    ArtifactRevisionGQLFilterInputDTO,
    ArtifactRevisionGQLOrderByInputDTO,
    ArtifactRevisionRemoteStatusFilterDTO,
    ArtifactRevisionStatusFilterDTO,
    DelegateeTargetInput,
    DeleteArtifactsInput,
    ModelTargetInput,
    UpdateArtifactInput,
)
from ai.backend.common.dto.manager.v2.artifact.response import (
    AdminSearchArtifactRevisionsPayload,
    AdminSearchArtifactsPayload,
    ArtifactNode,
    ArtifactRevisionNode,
    DeleteArtifactsPayload,
    UpdateArtifactPayload,
)
from ai.backend.common.dto.manager.v2.artifact.types import (
    ArtifactAvailability,
    ArtifactAvailabilityFilter,
    ArtifactOrderField,
    ArtifactRevisionOrderField,
    ArtifactStatus,
    ArtifactType,
    ArtifactTypeFilter,
    OrderDirection,
)
from ai.backend.manager.api.adapter_options.pagination.pagination import PaginationSpec
from ai.backend.manager.api.adapters.base import BaseAdapter
from ai.backend.manager.data.artifact.types import (
    ArtifactAvailability as DataArtifactAvailability,
)
from ai.backend.manager.data.artifact.types import (
    ArtifactData,
    ArtifactDataWithRevisions,
    ArtifactRevisionData,
)
from ai.backend.manager.data.artifact.types import (
    ArtifactRemoteStatus as DataArtifactRemoteStatus,
)
from ai.backend.manager.data.artifact.types import (
    ArtifactStatus as DataArtifactStatus,
)
from ai.backend.manager.data.artifact.types import (
    ArtifactType as DataArtifactType,
)
from ai.backend.manager.data.artifact.types import (
    DelegateeTarget as ServiceDelegateeTarget,
)
from ai.backend.manager.models.artifact.row import ArtifactRow
from ai.backend.manager.models.artifact.searchable_fields import ArtifactSearchableFields
from ai.backend.manager.models.artifact.searchers import ArtifactSearcher
from ai.backend.manager.models.artifact.updaters import ArtifactUpdater
from ai.backend.manager.models.artifact_revision.row import ArtifactRevisionRow
from ai.backend.manager.models.artifact_revision.searchable_fields import (
    ArtifactRevisionSearchableFields,
)
from ai.backend.manager.models.artifact_revision.searchers import ArtifactRevisionSearcher
from ai.backend.manager.models.clauses import QueryCondition, QueryOrder
from ai.backend.manager.models.condition_utils import combine_conditions_or, negate_conditions
from ai.backend.manager.services.artifact.actions.bulk_get import BulkGetArtifactsAction
from ai.backend.manager.services.artifact.actions.delegate_scan import (
    DelegateScanArtifactsAction,
    DelegateScanArtifactsActionResult,
)
from ai.backend.manager.services.artifact.actions.delete_multi import DeleteArtifactsAction
from ai.backend.manager.services.artifact.actions.get import GetArtifactAction
from ai.backend.manager.services.artifact.actions.get_revisions import (
    GetArtifactRevisionsAction,
)
from ai.backend.manager.services.artifact.actions.restore_multi import (
    RestoreArtifactsAction,
    RestoreArtifactsActionResult,
)
from ai.backend.manager.services.artifact.actions.retrieve_model_multi import (
    RetrieveModelsAction,
    RetrieveModelsActionResult,
)
from ai.backend.manager.services.artifact.actions.scan import (
    ScanArtifactsAction,
    ScanArtifactsActionResult,
)
from ai.backend.manager.services.artifact.actions.search import SearchArtifactsAction
from ai.backend.manager.services.artifact.actions.update import UpdateArtifactAction
from ai.backend.manager.services.artifact.processors import ArtifactProcessors
from ai.backend.manager.services.artifact.revision.actions.approve import (
    ApproveArtifactRevisionAction,
)
from ai.backend.manager.services.artifact.revision.actions.bulk_get import (
    BulkGetArtifactRevisionsAction,
)
from ai.backend.manager.services.artifact.revision.actions.cancel_import import CancelImportAction
from ai.backend.manager.services.artifact.revision.actions.cleanup import (
    CleanupArtifactRevisionAction,
)
from ai.backend.manager.services.artifact.revision.actions.delegate_import_revision_batch import (
    DelegateImportArtifactRevisionBatchAction,
)
from ai.backend.manager.services.artifact.revision.actions.get import GetArtifactRevisionAction
from ai.backend.manager.services.artifact.revision.actions.import_revision import (
    ImportArtifactRevisionAction,
)
from ai.backend.manager.services.artifact.revision.actions.reject import (
    RejectArtifactRevisionAction,
)
from ai.backend.manager.services.artifact.revision.actions.search import (
    SearchArtifactRevisionsAction,
)
from ai.backend.manager.types import OptionalState, TriState


@lru_cache(maxsize=1)
def _get_artifact_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=ArtifactSearchableFields.own.id.order.apply(ascending=False),
        cursor_column=ArtifactRow.id,
    )


@lru_cache(maxsize=1)
def _get_artifact_revision_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=ArtifactRevisionSearchableFields.own.field_id.order.apply(ascending=False),
        cursor_column=ArtifactRevisionRow.id,
    )


class ArtifactAdapter(BaseAdapter):
    """Adapter for artifact domain operations."""

    _artifact: ArtifactProcessors

    def __init__(self, artifact: ArtifactProcessors) -> None:
        self._artifact = artifact

    async def admin_search(
        self,
        input: AdminSearchArtifactsInput,
    ) -> AdminSearchArtifactsPayload:
        """Search artifacts (admin, no scope) with filters, orders, and pagination."""
        action_result = await self._artifact.search_artifacts.run(
            SearchArtifactsAction(searcher=self.build_searcher(input))
        )

        return AdminSearchArtifactsPayload(
            items=[self._data_to_dto(item) for item in action_result.data],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    async def admin_search_gql(
        self,
        input: AdminSearchArtifactsGQLInput,
        base_conditions: list[QueryCondition] | None = None,
    ) -> AdminSearchArtifactsPayload:
        """Search artifacts using GQL filter DTOs with cursor and offset pagination."""
        conditions: list[QueryCondition] = list(base_conditions or [])
        if input.filter is not None:
            conditions.extend(self._convert_gql_filter(input.filter))

        orders = self._convert_gql_orders(input.order) if input.order is not None else []
        searcher = self._build_searcher(
            ArtifactSearcher,
            pagination_spec=_get_artifact_pagination_spec(),
            conditions=conditions,
            orders=orders,
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )
        action_result = await self._artifact.search_artifacts.run(
            SearchArtifactsAction(searcher=searcher)
        )

        return AdminSearchArtifactsPayload(
            items=[self._data_to_dto(item) for item in action_result.data],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    def _build_revision_searcher(
        self, input: AdminSearchArtifactRevisionsInput
    ) -> ArtifactRevisionSearcher:
        conditions: list[QueryCondition] = []
        if input.filter is not None:
            conditions.extend(self._convert_gql_revision_filter(input.filter))

        orders = self._convert_gql_revision_orders(input.order) if input.order is not None else []
        return self._build_searcher(
            ArtifactRevisionSearcher,
            pagination_spec=_get_artifact_revision_pagination_spec(),
            conditions=conditions,
            orders=orders,
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )

    async def search_revisions_gql(
        self,
        input: AdminSearchArtifactRevisionsInput,
    ) -> AdminSearchArtifactRevisionsPayload:
        """Search artifact revisions using GQL filter DTOs with cursor and offset pagination."""
        action_result = await self._artifact.revision.search_revision.run(
            SearchArtifactRevisionsAction(searcher=self._build_revision_searcher(input))
        )

        return AdminSearchArtifactRevisionsPayload(
            items=[self._revision_data_to_dto(item) for item in action_result.data],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    async def search_revisions_of_artifact_gql(
        self,
        artifact_id: ArtifactID,
        input: AdminSearchArtifactRevisionsInput,
    ) -> AdminSearchArtifactRevisionsPayload:
        """Search the revisions one artifact holds, authorized against that artifact."""
        action_result = await self._artifact.get_revisions.run(
            GetArtifactRevisionsAction(
                artifact_ids=[artifact_id],
                searcher=self._build_revision_searcher(input),
            )
        )

        return AdminSearchArtifactRevisionsPayload(
            items=[self._revision_data_to_dto(item) for item in action_result.items],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    async def batch_load_by_ids(
        self, artifact_ids: Sequence[UUID]
    ) -> list[ArtifactNode | Exception | None]:
        """Batch load artifacts by their IDs for DataLoader use, checked per artifact."""
        if not artifact_ids:
            return []
        result = await self._artifact.bulk_get.run(
            BulkGetArtifactsAction(ids=[ArtifactID(artifact_id) for artifact_id in artifact_ids])
        )
        return [
            self._data_to_dto(item.value)
            if item.value is not None
            else self.batch_load_failure(item.error)
            for item in result.items
        ]

    async def batch_load_revisions_by_ids(
        self, revision_ids: Sequence[ArtifactRevisionID]
    ) -> list[ArtifactRevisionNode | Exception | None]:
        """Batch load artifact revisions by their IDs for DataLoader use, checked per artifact."""
        if not revision_ids:
            return []
        ids = [ArtifactRevisionID(revision_id) for revision_id in revision_ids]
        return await self.batch_load_fields(
            self._artifact.revision.bulk_get,
            BulkGetArtifactRevisionsAction(ids=ids),
            ids,
            self._revision_data_to_dto,
        )

    async def get(self, artifact_id: UUID) -> ArtifactNode:
        """Retrieve a single artifact by ID."""
        action_result = await self._artifact.get.run(
            GetArtifactAction(artifact_id=ArtifactID(artifact_id))
        )
        return self._data_to_dto(action_result.result)

    async def update(
        self,
        input: UpdateArtifactInput,
        artifact_id: UUID,
    ) -> UpdateArtifactPayload:
        """Update artifact metadata (readonly flag and description)."""
        updater = ArtifactUpdater(
            artifact_id=ArtifactID(artifact_id),
            readonly=OptionalState.from_unset(input.readonly),
            description=TriState.from_unset(input.description),
        )
        action_result = await self._artifact.update.run(
            UpdateArtifactAction(artifact_id=ArtifactID(artifact_id), updater=updater)
        )
        return UpdateArtifactPayload(artifact=self._data_to_dto(action_result.result))

    async def delete(self, input: DeleteArtifactsInput) -> DeleteArtifactsPayload:
        """Delete multiple artifacts by ID."""
        action_result = await self._artifact.delete_artifacts.run(
            DeleteArtifactsAction(artifact_ids=input.artifact_ids)
        )
        return DeleteArtifactsPayload(
            artifacts=[self._data_to_dto(item) for item in action_result.artifacts]
        )

    async def get_revision(self, artifact_revision_id: UUID) -> ArtifactRevisionNode:
        """Retrieve a single artifact revision by ID."""
        action_result = await self._artifact.revision.get.run(
            GetArtifactRevisionAction(artifact_revision_id=ArtifactRevisionID(artifact_revision_id))
        )
        return self._revision_data_to_dto(action_result.data)

    async def scan(
        self,
        artifact_type: DataArtifactType | None,
        registry_id: UUID | None,
        limit: int | None,
        order: ModelSortKey | None,
        search: str | None,
    ) -> list[ArtifactNode]:
        """Scan external registries to discover available artifacts."""
        action_result: ScanArtifactsActionResult = await self._artifact.scan.run(
            ScanArtifactsAction(
                artifact_type=artifact_type,
                registry_id=ArtifactRegistryID(registry_id) if registry_id is not None else None,
                limit=limit,
                order=order,
                search=search,
            )
        )
        return [self._data_to_dto(item) for item in action_result.result]

    async def import_revision(
        self,
        artifact_revision_id: UUID,
        vfolder_id: UUID | None,
        storage_prefix: str | None,
        force: bool,
    ) -> tuple[ArtifactRevisionNode, UUID | None]:
        """Import a single artifact revision and return (revision_node, task_id)."""
        action_result = await self._artifact.revision.import_revision.run(
            ImportArtifactRevisionAction(
                artifact_revision_id=ArtifactRevisionID(artifact_revision_id),
                vfolder_id=vfolder_id,
                storage_prefix=storage_prefix,
                force=force,
            )
        )
        return self._revision_data_to_dto(action_result.result), action_result.task_id

    async def delegate_scan(
        self,
        delegator_reservoir_id: UUID | None,
        delegatee_target: DelegateeTargetInput | None,
        artifact_type: DataArtifactType | None,
        limit: int | None,
        order: ModelSortKey | None,
        search: str | None,
    ) -> list[ArtifactNode]:
        """Trigger artifact scanning on a remote reservoir registry."""
        service_target = (
            ServiceDelegateeTarget(
                delegatee_reservoir_id=delegatee_target.delegatee_reservoir_id,
                target_registry_id=ArtifactRegistryID(delegatee_target.target_registry_id)
                if delegatee_target.target_registry_id is not None
                else None,
            )
            if delegatee_target is not None
            else None
        )
        action_result: DelegateScanArtifactsActionResult = await self._artifact.delegate_scan.run(
            DelegateScanArtifactsAction(
                delegator_reservoir_id=delegator_reservoir_id,
                delegatee_target=service_target,
                artifact_type=artifact_type,
                limit=limit,
                order=order,
                search=search,
            )
        )
        return [self._data_to_dto(item) for item in action_result.result]

    async def delegate_import_batch(
        self,
        delegator_reservoir_id: UUID | None,
        delegatee_target: DelegateeTargetInput | None,
        artifact_type: DataArtifactType | None,
        artifact_revision_ids: list[UUID],
        force: bool,
    ) -> tuple[list[ArtifactRevisionNode], list[UUID | None]]:
        """Import artifact revisions from a remote reservoir registry in batch.

        Returns a tuple of (revision_nodes, task_ids).
        """
        service_target = (
            ServiceDelegateeTarget(
                delegatee_reservoir_id=delegatee_target.delegatee_reservoir_id,
                target_registry_id=ArtifactRegistryID(delegatee_target.target_registry_id)
                if delegatee_target.target_registry_id is not None
                else None,
            )
            if delegatee_target is not None
            else None
        )
        action_result = await self._artifact.revision.delegate_import_revision_batch.run(
            DelegateImportArtifactRevisionBatchAction(
                delegator_reservoir_id=delegator_reservoir_id,
                delegatee_target=service_target,
                artifact_type=artifact_type,
                artifact_revision_ids=artifact_revision_ids,
                force=force,
            )
        )
        revision_nodes = [self._revision_data_to_dto(r) for r in action_result.result]
        return revision_nodes, action_result.task_ids

    async def cleanup_revision(self, artifact_revision_id: UUID) -> ArtifactRevisionNode:
        """Clean up stored artifact revision data and revert to SCANNED status."""
        action_result = await self._artifact.revision.cleanup.run(
            CleanupArtifactRevisionAction(
                artifact_revision_id=ArtifactRevisionID(artifact_revision_id)
            )
        )
        return self._revision_data_to_dto(action_result.result)

    async def restore(self, artifact_ids: list[UUID]) -> list[ArtifactNode]:
        """Restore previously deleted artifacts."""
        action_result: RestoreArtifactsActionResult = await self._artifact.restore_artifacts.run(
            RestoreArtifactsAction(artifact_ids=artifact_ids)
        )
        return [self._data_to_dto(item) for item in action_result.artifacts]

    async def cancel_import(self, artifact_revision_id: UUID) -> ArtifactRevisionNode:
        """Cancel an in-progress artifact import and revert to SCANNED status."""
        action_result = await self._artifact.revision.cancel_import.run(
            CancelImportAction(artifact_revision_id=ArtifactRevisionID(artifact_revision_id))
        )
        return self._revision_data_to_dto(action_result.result)

    async def approve_revision(self, artifact_revision_id: UUID) -> ArtifactRevisionNode:
        """Approve an artifact revision for general use."""
        action_result = await self._artifact.revision.approve.run(
            ApproveArtifactRevisionAction(
                artifact_revision_id=ArtifactRevisionID(artifact_revision_id)
            )
        )
        return self._revision_data_to_dto(action_result.result)

    async def reject_revision(self, artifact_revision_id: UUID) -> ArtifactRevisionNode:
        """Reject an artifact revision, preventing its use."""
        action_result = await self._artifact.revision.reject.run(
            RejectArtifactRevisionAction(
                artifact_revision_id=ArtifactRevisionID(artifact_revision_id)
            )
        )
        return self._revision_data_to_dto(action_result.result)

    async def retrieve_models(
        self,
        models: list[ModelTargetInput],
        registry_id: UUID | None,
    ) -> list[ArtifactNode]:
        """Perform detailed scanning of specific models from external registries."""
        storage_models = [
            StorageModelTarget(model_id=m.model_id, revision=m.revision) for m in models
        ]
        action_result: RetrieveModelsActionResult = await self._artifact.retrieve_models.run(
            RetrieveModelsAction(
                models=storage_models,
                registry_id=ArtifactRegistryID(registry_id) if registry_id is not None else None,
            )
        )
        return [self._data_with_revisions_to_dto(item) for item in action_result.result]

    def build_searcher(self, input: AdminSearchArtifactsInput) -> ArtifactSearcher:
        """Build an artifact searcher from the search input DTO."""
        conditions = self._convert_filter(input.filter) if input.filter else []
        orders = self._convert_orders(input.order) if input.order else []
        return self._build_searcher(
            ArtifactSearcher,
            pagination_spec=_get_artifact_pagination_spec(),
            conditions=conditions,
            orders=orders,
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )

    def _convert_gql_filter(
        self,
        filter: ArtifactGQLFilterInputDTO,
    ) -> list[QueryCondition]:
        """Convert a GQL-facing ArtifactGQLFilterInputDTO to query conditions."""
        fields = ArtifactSearchableFields.own
        conditions: list[QueryCondition] = []

        if filter.type:
            conditions.append(
                fields.type.filter.in_([DataArtifactType(t.value) for t in filter.type])
            )
        conditions.extend(self.apply_string_filter(filter.name, fields.name.filter))
        conditions.extend(self.apply_string_filter(filter.registry, fields.registry_type.filter))
        conditions.extend(
            self.apply_string_filter(filter.source, fields.source_registry_type.filter)
        )
        if filter.availability:
            conditions.append(
                fields.availability.filter.in_([
                    DataArtifactAvailability(a.value) for a in filter.availability
                ])
            )

        if filter.AND:
            for sub_filter in filter.AND:
                conditions.extend(self._convert_gql_filter(sub_filter))
        if filter.OR:
            or_conditions: list[QueryCondition] = []
            for sub_filter in filter.OR:
                or_conditions.extend(self._convert_gql_filter(sub_filter))
            if or_conditions:
                conditions.append(combine_conditions_or(or_conditions))
        if filter.NOT:
            not_conditions: list[QueryCondition] = []
            for sub_filter in filter.NOT:
                not_conditions.extend(self._convert_gql_filter(sub_filter))
            if not_conditions:
                conditions.append(negate_conditions(not_conditions))

        return conditions

    def _convert_gql_orders(
        self,
        orders: list[ArtifactGQLOrderByInputDTO],
    ) -> list[QueryOrder]:
        """Convert GQL order DTOs to query orders."""
        return self._artifact_orders([
            (order.field, order.direction == OrderDirection.ASC) for order in orders
        ])

    def _convert_gql_revision_filter(
        self,
        filter: ArtifactRevisionGQLFilterInputDTO,
    ) -> list[QueryCondition]:
        """Convert a GQL-facing ArtifactRevisionGQLFilterInputDTO to query conditions."""
        fields = ArtifactRevisionSearchableFields.own
        conditions: list[QueryCondition] = []

        if filter.status is not None:
            conditions.extend(self._convert_revision_status_filter(filter.status))
        if filter.remote_status is not None:
            conditions.extend(self._convert_revision_remote_status_filter(filter.remote_status))
        conditions.extend(self.apply_string_filter(filter.version, fields.version.filter))
        if filter.artifact_id is not None:
            conditions.extend(self.apply_uuid_filter(filter.artifact_id, fields.artifact_id.filter))
        conditions.extend(self.apply_int_filter(filter.size, fields.size.filter))

        if filter.AND:
            for sub_filter in filter.AND:
                conditions.extend(self._convert_gql_revision_filter(sub_filter))
        if filter.OR:
            or_conditions: list[QueryCondition] = []
            for sub_filter in filter.OR:
                or_conditions.extend(self._convert_gql_revision_filter(sub_filter))
            if or_conditions:
                conditions.append(combine_conditions_or(or_conditions))
        if filter.NOT:
            not_conditions: list[QueryCondition] = []
            for sub_filter in filter.NOT:
                not_conditions.extend(self._convert_gql_revision_filter(sub_filter))
            if not_conditions:
                conditions.append(negate_conditions(not_conditions))

        return conditions

    @staticmethod
    def _convert_revision_status_filter(
        sf: ArtifactRevisionStatusFilterDTO,
    ) -> list[QueryCondition]:
        statuses: list[DataArtifactStatus] = []
        if sf.in_ is not None:
            statuses.extend([DataArtifactStatus(s.value) for s in sf.in_])
        if sf.equals is not None:
            statuses.append(DataArtifactStatus(sf.equals.value))
        if not statuses:
            return []
        return [ArtifactRevisionSearchableFields.own.status.filter.in_(statuses)]

    @staticmethod
    def _convert_revision_remote_status_filter(
        rsf: ArtifactRevisionRemoteStatusFilterDTO,
    ) -> list[QueryCondition]:
        remote_statuses: list[DataArtifactRemoteStatus] = []
        if rsf.in_ is not None:
            remote_statuses.extend([DataArtifactRemoteStatus(s.value) for s in rsf.in_])
        if rsf.equals is not None:
            remote_statuses.append(DataArtifactRemoteStatus(rsf.equals.value))
        if not remote_statuses:
            return []
        return [ArtifactRevisionSearchableFields.own.remote_status.filter.in_(remote_statuses)]

    @staticmethod
    def _convert_gql_revision_orders(
        orders: list[ArtifactRevisionGQLOrderByInputDTO],
    ) -> list[QueryOrder]:
        """Convert GQL revision order DTOs to query orders."""
        fields = ArtifactRevisionSearchableFields.own
        result: list[QueryOrder] = []
        for order in orders:
            ascending = order.direction == OrderDirection.ASC
            match order.field:
                case ArtifactRevisionOrderField.VERSION:
                    result.append(fields.version.order.apply(ascending))
                case ArtifactRevisionOrderField.STATUS:
                    result.append(fields.status.order.apply(ascending))
                case ArtifactRevisionOrderField.SIZE:
                    result.append(fields.size.order.apply(ascending))
                case ArtifactRevisionOrderField.CREATED_AT:
                    result.append(fields.created_at.order.apply(ascending))
                case ArtifactRevisionOrderField.UPDATED_AT:
                    result.append(fields.updated_at.order.apply(ascending))
                case _:
                    assert_never(order.field)
        return result

    def _convert_filter(self, filter: ArtifactFilter) -> list[QueryCondition]:
        fields = ArtifactSearchableFields.own
        conditions: list[QueryCondition] = list(
            self.apply_string_filter(filter.name, fields.name.filter)
        )
        if filter.type is not None:
            conditions.extend(self._convert_type_filter(filter.type))
        if filter.availability is not None:
            conditions.extend(self._convert_availability_filter(filter.availability))
        return conditions

    @staticmethod
    def _convert_type_filter(tf: ArtifactTypeFilter) -> list[QueryCondition]:
        conditions_of = ArtifactSearchableFields.own.type.filter
        conditions: list[QueryCondition] = []
        if tf.equals is not None:
            conditions.append(conditions_of.equals(DataArtifactType(tf.equals)))
        if tf.in_ is not None:
            conditions.append(conditions_of.in_([DataArtifactType(t) for t in tf.in_]))
        if tf.not_equals is not None:
            conditions.append(conditions_of.not_equals(DataArtifactType(tf.not_equals)))
        if tf.not_in is not None:
            conditions.append(conditions_of.not_in([DataArtifactType(t) for t in tf.not_in]))
        return conditions

    @staticmethod
    def _convert_availability_filter(
        af: ArtifactAvailabilityFilter,
    ) -> list[QueryCondition]:
        conditions_of = ArtifactSearchableFields.own.availability.filter
        conditions: list[QueryCondition] = []
        if af.equals is not None:
            conditions.append(conditions_of.equals(DataArtifactAvailability(af.equals)))
        if af.in_ is not None:
            conditions.append(conditions_of.in_([DataArtifactAvailability(a) for a in af.in_]))
        if af.not_equals is not None:
            conditions.append(conditions_of.not_equals(DataArtifactAvailability(af.not_equals)))
        if af.not_in is not None:
            conditions.append(
                conditions_of.not_in([DataArtifactAvailability(a) for a in af.not_in])
            )
        return conditions

    def _convert_orders(self, order: list[ArtifactOrder]) -> list[QueryOrder]:
        return self._artifact_orders([(o.field, o.direction == OrderDirection.ASC) for o in order])

    @staticmethod
    def _artifact_orders(
        orders: list[tuple[ArtifactOrderField, bool]],
    ) -> list[QueryOrder]:
        """``SIZE`` belongs to the revisions, not the artifact, so it orders by nothing."""
        fields = ArtifactSearchableFields.own
        result: list[QueryOrder] = []
        for field, ascending in orders:
            match field:
                case ArtifactOrderField.NAME:
                    result.append(fields.name.order.apply(ascending))
                case ArtifactOrderField.TYPE:
                    result.append(fields.type.order.apply(ascending))
                case ArtifactOrderField.SCANNED_AT:
                    result.append(fields.scanned_at.order.apply(ascending))
                case ArtifactOrderField.UPDATED_AT:
                    result.append(fields.updated_at.order.apply(ascending))
                case ArtifactOrderField.SIZE:
                    continue
                case _:
                    assert_never(field)
        return result

    @staticmethod
    def _data_to_dto(data: ArtifactData) -> ArtifactNode:
        return ArtifactNode(
            id=data.id,
            entity_id=data.entity_id(),
            name=data.name,
            type=ArtifactType(data.type),
            description=data.description,
            registry_id=ArtifactRegistryID(data.registry_id)
            if data.registry_id is not None
            else None,
            source_registry_id=ArtifactRegistryID(data.source_registry_id)
            if data.source_registry_id is not None
            else None,
            registry_type=data.registry_type,
            source_registry_type=data.source_registry_type,
            availability=ArtifactAvailability(data.availability),
            scanned_at=data.scanned_at,
            updated_at=data.updated_at,
            readonly=data.readonly,
            extra=data.extra,
        )

    @staticmethod
    def _revision_data_to_dto(data: ArtifactRevisionData) -> ArtifactRevisionNode:
        return ArtifactRevisionNode(
            id=data.id,
            field_id=data.id,
            artifact_id=ArtifactID(data.artifact_id),
            version=data.version,
            size=str(data.size) if data.size is not None else None,
            status=ArtifactStatus(data.status),
            remote_status=data.remote_status,
            created_at=data.created_at,
            updated_at=data.updated_at,
            readme=data.readme,
        )

    @staticmethod
    def _data_with_revisions_to_dto(data: ArtifactDataWithRevisions) -> ArtifactNode:
        return ArtifactNode(
            id=data.id,
            entity_id=data.entity_id(),
            name=data.name,
            type=ArtifactType(data.type),
            description=data.description,
            registry_id=ArtifactRegistryID(data.registry_id)
            if data.registry_id is not None
            else None,
            source_registry_id=ArtifactRegistryID(data.source_registry_id)
            if data.source_registry_id is not None
            else None,
            registry_type=data.registry_type,
            source_registry_type=data.source_registry_type,
            availability=ArtifactAvailability(data.availability),
            scanned_at=data.scanned_at,
            updated_at=data.updated_at,
            readonly=data.readonly,
            extra=data.extra,
            revisions=[ArtifactAdapter._revision_data_to_dto(r) for r in data.revisions],
        )
