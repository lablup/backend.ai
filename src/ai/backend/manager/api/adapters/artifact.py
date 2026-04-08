"""Artifact adapter bridging DTOs and Processors."""

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from ai.backend.common.api_handlers import Sentinel
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
from ai.backend.manager.models.artifact.conditions import ArtifactConditions
from ai.backend.manager.models.artifact.orders import (
    DEFAULT_FORWARD_ORDER,
    TIEBREAKER_ORDER,
    resolve_order,
)
from ai.backend.manager.models.artifact.row import ArtifactRow
from ai.backend.manager.models.artifact_revision.conditions import ArtifactRevisionConditions
from ai.backend.manager.models.artifact_revision.orders import ArtifactRevisionOrders
from ai.backend.manager.models.artifact_revision.row import ArtifactRevisionRow
from ai.backend.manager.repositories.artifact.updaters import ArtifactUpdaterSpec
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    OffsetPagination,
    QueryCondition,
    QueryOrder,
    combine_conditions_or,
    negate_conditions,
)
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.services.artifact.actions.delegate_scan import (
    DelegateScanArtifactsAction,
    DelegateScanArtifactsActionResult,
)
from ai.backend.manager.services.artifact.actions.delete_multi import DeleteArtifactsAction
from ai.backend.manager.services.artifact.actions.get import GetArtifactAction
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
from ai.backend.manager.services.artifact_revision.actions.approve import (
    ApproveArtifactRevisionAction,
)
from ai.backend.manager.services.artifact_revision.actions.cancel_import import CancelImportAction
from ai.backend.manager.services.artifact_revision.actions.cleanup import (
    CleanupArtifactRevisionAction,
)
from ai.backend.manager.services.artifact_revision.actions.delegate_import_revision_batch import (
    DelegateImportArtifactRevisionBatchAction,
)
from ai.backend.manager.services.artifact_revision.actions.get import GetArtifactRevisionAction
from ai.backend.manager.services.artifact_revision.actions.import_revision import (
    ImportArtifactRevisionAction,
)
from ai.backend.manager.services.artifact_revision.actions.reject import (
    RejectArtifactRevisionAction,
)
from ai.backend.manager.services.artifact_revision.actions.search import (
    SearchArtifactRevisionsAction,
)
from ai.backend.manager.types import TriState

from .base import BaseAdapter

DEFAULT_PAGINATION_LIMIT = 10


class ArtifactAdapter(BaseAdapter):
    """Adapter for artifact domain operations."""

    async def admin_search(
        self,
        input: AdminSearchArtifactsInput,
    ) -> AdminSearchArtifactsPayload:
        """Search artifacts (admin, no scope) with filters, orders, and pagination."""
        querier = self.build_querier(input)

        action_result = await self._processors.artifact.search_artifacts.wait_for_complete(
            SearchArtifactsAction(querier=querier)
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

        orders: list[QueryOrder] = []
        if input.order is not None:
            orders.extend(self._convert_gql_orders(input.order))
        else:
            orders.append(DEFAULT_FORWARD_ORDER)
        orders.append(TIEBREAKER_ORDER)

        pagination = self._build_gql_pagination_artifacts(input)
        querier = BatchQuerier(conditions=conditions, orders=orders, pagination=pagination)

        action_result = await self._processors.artifact.search_artifacts.wait_for_complete(
            SearchArtifactsAction(querier=querier)
        )

        return AdminSearchArtifactsPayload(
            items=[self._data_to_dto(item) for item in action_result.data],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    async def search_revisions_gql(
        self,
        input: AdminSearchArtifactRevisionsInput,
        base_conditions: list[QueryCondition] | None = None,
    ) -> AdminSearchArtifactRevisionsPayload:
        """Search artifact revisions using GQL filter DTOs with cursor and offset pagination."""
        conditions: list[QueryCondition] = list(base_conditions or [])
        if input.filter is not None:
            conditions.extend(self._convert_gql_revision_filter(input.filter))

        orders: list[QueryOrder] = []
        if input.order is not None:
            orders.extend(self._convert_gql_revision_orders(input.order))
        else:
            orders.append(ArtifactRevisionRow.id.desc())
        orders.append(ArtifactRevisionRow.id.asc())  # tiebreaker

        pagination = self._build_gql_pagination_revisions(input)
        querier = BatchQuerier(conditions=conditions, orders=orders, pagination=pagination)

        action_result = await self._processors.artifact_revision.search_revision.wait_for_complete(
            SearchArtifactRevisionsAction(querier=querier)
        )

        return AdminSearchArtifactRevisionsPayload(
            items=[self._revision_data_to_dto(item) for item in action_result.data],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    async def batch_load_by_ids(self, artifact_ids: Sequence[UUID]) -> list[ArtifactNode | None]:
        """Batch load artifacts by their IDs for DataLoader use.

        Returns ArtifactNode DTOs in the same order as the input artifact_ids list.
        """
        if not artifact_ids:
            return []

        querier = BatchQuerier(
            pagination=OffsetPagination(limit=len(artifact_ids)),
            conditions=[ArtifactConditions.by_ids(artifact_ids)],
        )

        action_result = await self._processors.artifact.search_artifacts.wait_for_complete(
            SearchArtifactsAction(querier=querier)
        )

        artifact_map = {item.id: self._data_to_dto(item) for item in action_result.data}
        return [artifact_map.get(artifact_id) for artifact_id in artifact_ids]

    async def batch_load_revisions_by_ids(
        self, revision_ids: Sequence[UUID]
    ) -> list[ArtifactRevisionNode | None]:
        """Batch load artifact revisions by their IDs for DataLoader use.

        Returns ArtifactRevisionNode DTOs in the same order as the input revision_ids list.
        """
        if not revision_ids:
            return []

        querier = BatchQuerier(
            pagination=OffsetPagination(limit=len(revision_ids)),
            conditions=[ArtifactRevisionConditions.by_ids(revision_ids)],
        )

        action_result = await self._processors.artifact_revision.search_revision.wait_for_complete(
            SearchArtifactRevisionsAction(querier=querier)
        )

        revision_map = {item.id: self._revision_data_to_dto(item) for item in action_result.data}
        return [revision_map.get(revision_id) for revision_id in revision_ids]

    async def get(self, artifact_id: UUID) -> ArtifactNode:
        """Retrieve a single artifact by ID."""
        action_result = await self._processors.artifact.get.wait_for_complete(
            GetArtifactAction(artifact_id=artifact_id)
        )
        return self._data_to_dto(action_result.result)

    async def update(
        self,
        input: UpdateArtifactInput,
        artifact_id: UUID,
    ) -> UpdateArtifactPayload:
        """Update artifact metadata (readonly flag and description)."""
        spec = ArtifactUpdaterSpec(
            readonly=(
                TriState.update(input.readonly)
                if input.readonly is not None
                else TriState[bool].nop()
            ),
            description=(
                TriState[str].nop()
                if isinstance(input.description, Sentinel)
                else TriState[str].from_graphql(input.description)
            ),
        )
        updater: Updater[ArtifactRow] = Updater(spec=spec, pk_value=artifact_id)
        action_result = await self._processors.artifact.update.wait_for_complete(
            UpdateArtifactAction(updater=updater)
        )
        return UpdateArtifactPayload(artifact=self._data_to_dto(action_result.result))

    async def delete(self, input: DeleteArtifactsInput) -> DeleteArtifactsPayload:
        """Delete multiple artifacts by ID."""
        action_result = await self._processors.artifact.delete_artifacts.wait_for_complete(
            DeleteArtifactsAction(artifact_ids=input.artifact_ids)
        )
        return DeleteArtifactsPayload(
            artifacts=[self._data_to_dto(item) for item in action_result.artifacts]
        )

    async def get_revision(self, artifact_revision_id: UUID) -> ArtifactRevisionNode:
        """Retrieve a single artifact revision by ID."""
        action_result = await self._processors.artifact_revision.get.wait_for_complete(
            GetArtifactRevisionAction(artifact_revision_id=artifact_revision_id)
        )
        return self._revision_data_to_dto(action_result.revision)

    async def scan(
        self,
        artifact_type: DataArtifactType | None,
        registry_id: UUID | None,
        limit: int | None,
        order: ModelSortKey | None,
        search: str | None,
    ) -> list[ArtifactNode]:
        """Scan external registries to discover available artifacts."""
        action_result: ScanArtifactsActionResult = (
            await self._processors.artifact.scan.wait_for_complete(
                ScanArtifactsAction(
                    artifact_type=artifact_type,
                    registry_id=registry_id,
                    limit=limit,
                    order=order,
                    search=search,
                )
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
        action_result = await self._processors.artifact_revision.import_revision.wait_for_complete(
            ImportArtifactRevisionAction(
                artifact_revision_id=artifact_revision_id,
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
                target_registry_id=delegatee_target.target_registry_id,
            )
            if delegatee_target is not None
            else None
        )
        action_result: DelegateScanArtifactsActionResult = (
            await self._processors.artifact.delegate_scan.wait_for_complete(
                DelegateScanArtifactsAction(
                    delegator_reservoir_id=delegator_reservoir_id,
                    delegatee_target=service_target,
                    artifact_type=artifact_type,
                    limit=limit,
                    order=order,
                    search=search,
                )
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
                target_registry_id=delegatee_target.target_registry_id,
            )
            if delegatee_target is not None
            else None
        )
        action_result = await self._processors.artifact_revision.delegate_import_revision_batch.wait_for_complete(
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
        action_result = await self._processors.artifact_revision.cleanup.wait_for_complete(
            CleanupArtifactRevisionAction(artifact_revision_id=artifact_revision_id)
        )
        return self._revision_data_to_dto(action_result.result)

    async def restore(self, artifact_ids: list[UUID]) -> list[ArtifactNode]:
        """Restore previously deleted artifacts."""
        action_result: RestoreArtifactsActionResult = (
            await self._processors.artifact.restore_artifacts.wait_for_complete(
                RestoreArtifactsAction(artifact_ids=artifact_ids)
            )
        )
        return [self._data_to_dto(item) for item in action_result.artifacts]

    async def cancel_import(self, artifact_revision_id: UUID) -> ArtifactRevisionNode:
        """Cancel an in-progress artifact import and revert to SCANNED status."""
        action_result = await self._processors.artifact_revision.cancel_import.wait_for_complete(
            CancelImportAction(artifact_revision_id=artifact_revision_id)
        )
        return self._revision_data_to_dto(action_result.result)

    async def approve_revision(self, artifact_revision_id: UUID) -> ArtifactRevisionNode:
        """Approve an artifact revision for general use."""
        action_result = await self._processors.artifact_revision.approve.wait_for_complete(
            ApproveArtifactRevisionAction(artifact_revision_id=artifact_revision_id)
        )
        return self._revision_data_to_dto(action_result.result)

    async def reject_revision(self, artifact_revision_id: UUID) -> ArtifactRevisionNode:
        """Reject an artifact revision, preventing its use."""
        action_result = await self._processors.artifact_revision.reject.wait_for_complete(
            RejectArtifactRevisionAction(artifact_revision_id=artifact_revision_id)
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
        action_result: RetrieveModelsActionResult = (
            await self._processors.artifact.retrieve_models.wait_for_complete(
                RetrieveModelsAction(models=storage_models, registry_id=registry_id)
            )
        )
        return [self._data_with_revisions_to_dto(item) for item in action_result.result]

    def build_querier(self, input: AdminSearchArtifactsInput) -> BatchQuerier:
        """Build a BatchQuerier from the search input DTO."""
        conditions = self._convert_filter(input.filter) if input.filter else []
        orders = self._convert_orders(input.order) if input.order else [DEFAULT_FORWARD_ORDER]
        orders.append(TIEBREAKER_ORDER)
        pagination = self._build_pagination(input)
        return BatchQuerier(conditions=conditions, orders=orders, pagination=pagination)

    def _convert_gql_filter(
        self,
        filter: ArtifactGQLFilterInputDTO,
    ) -> list[QueryCondition]:
        """Convert a GQL-facing ArtifactGQLFilterInputDTO to query conditions."""
        conditions: list[QueryCondition] = []

        if filter.type:
            conditions.append(
                ArtifactConditions.by_types([DataArtifactType(t.value) for t in filter.type])
            )
        if filter.name is not None:
            condition = self.convert_string_filter(
                filter.name,
                contains_factory=ArtifactConditions.by_name_contains,
                equals_factory=ArtifactConditions.by_name_equals,
                starts_with_factory=ArtifactConditions.by_name_starts_with,
                ends_with_factory=ArtifactConditions.by_name_ends_with,
                in_factory=ArtifactConditions.by_name_in,
            )
            if condition is not None:
                conditions.append(condition)
        if filter.registry is not None:
            condition = self.convert_string_filter(
                filter.registry,
                contains_factory=ArtifactConditions.by_registry_contains,
                equals_factory=ArtifactConditions.by_registry_equals,
                starts_with_factory=ArtifactConditions.by_registry_starts_with,
                ends_with_factory=ArtifactConditions.by_registry_ends_with,
                in_factory=ArtifactConditions.by_registry_in,
            )
            if condition is not None:
                conditions.append(condition)
        if filter.source is not None:
            condition = self.convert_string_filter(
                filter.source,
                contains_factory=ArtifactConditions.by_source_contains,
                equals_factory=ArtifactConditions.by_source_equals,
                starts_with_factory=ArtifactConditions.by_source_starts_with,
                ends_with_factory=ArtifactConditions.by_source_ends_with,
                in_factory=ArtifactConditions.by_source_in,
            )
            if condition is not None:
                conditions.append(condition)
        if filter.availability:
            conditions.append(
                ArtifactConditions.by_availability([
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
        result: list[QueryOrder] = []
        for order in orders:
            ascending = order.direction == OrderDirection.ASC
            match order.field:
                case ArtifactOrderField.NAME:
                    result.append(ArtifactRow.name.asc() if ascending else ArtifactRow.name.desc())
                case ArtifactOrderField.TYPE:
                    result.append(ArtifactRow.type.asc() if ascending else ArtifactRow.type.desc())
                case ArtifactOrderField.SCANNED_AT:
                    result.append(
                        ArtifactRow.scanned_at.asc() if ascending else ArtifactRow.scanned_at.desc()
                    )
                case ArtifactOrderField.UPDATED_AT:
                    result.append(
                        ArtifactRow.updated_at.asc() if ascending else ArtifactRow.updated_at.desc()
                    )
                case ArtifactOrderField.SIZE:
                    result.append(
                        ArtifactRow.updated_at.asc() if ascending else ArtifactRow.updated_at.desc()
                    )
        return result

    def _convert_gql_revision_filter(
        self,
        filter: ArtifactRevisionGQLFilterInputDTO,
    ) -> list[QueryCondition]:
        """Convert a GQL-facing ArtifactRevisionGQLFilterInputDTO to query conditions."""
        conditions: list[QueryCondition] = []

        if filter.status is not None:
            conditions.extend(self._convert_revision_status_filter(filter.status))
        if filter.remote_status is not None:
            conditions.extend(self._convert_revision_remote_status_filter(filter.remote_status))
        if filter.version is not None:
            condition = self.convert_string_filter(
                filter.version,
                contains_factory=ArtifactRevisionConditions.by_version_contains,
                equals_factory=ArtifactRevisionConditions.by_version_equals,
                starts_with_factory=ArtifactRevisionConditions.by_version_starts_with,
                ends_with_factory=ArtifactRevisionConditions.by_version_ends_with,
                in_factory=ArtifactRevisionConditions.by_version_in,
            )
            if condition is not None:
                conditions.append(condition)
        if filter.artifact_id is not None:
            if filter.artifact_id.equals is not None:
                conditions.append(
                    ArtifactRevisionConditions.by_artifact_id(filter.artifact_id.equals)
                )
            elif filter.artifact_id.in_ is not None:
                conditions.append(
                    ArtifactRevisionConditions.by_artifact_ids(filter.artifact_id.in_)
                )
        if filter.size is not None:
            sf = filter.size
            if sf.equals is not None:
                conditions.append(ArtifactRevisionConditions.by_size_equals(sf.equals))
            if sf.not_equals is not None:
                conditions.append(ArtifactRevisionConditions.by_size_not_equals(sf.not_equals))
            if sf.greater_than is not None:
                conditions.append(ArtifactRevisionConditions.by_size_greater_than(sf.greater_than))
            if sf.greater_than_or_equal is not None:
                conditions.append(
                    ArtifactRevisionConditions.by_size_greater_than_or_equal(
                        sf.greater_than_or_equal
                    )
                )
            if sf.less_than is not None:
                conditions.append(ArtifactRevisionConditions.by_size_less_than(sf.less_than))
            if sf.less_than_or_equal is not None:
                conditions.append(
                    ArtifactRevisionConditions.by_size_less_than_or_equal(sf.less_than_or_equal)
                )

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
        conditions: list[QueryCondition] = []
        statuses: list[DataArtifactStatus] = []
        if sf.in_ is not None:
            statuses.extend([DataArtifactStatus(s.value) for s in sf.in_])
        if sf.equals is not None:
            statuses.append(DataArtifactStatus(sf.equals.value))
        if statuses:
            conditions.append(ArtifactRevisionConditions.by_statuses(statuses))
        return conditions

    @staticmethod
    def _convert_revision_remote_status_filter(
        rsf: ArtifactRevisionRemoteStatusFilterDTO,
    ) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
        remote_statuses: list[DataArtifactRemoteStatus] = []
        if rsf.in_ is not None:
            remote_statuses.extend([DataArtifactRemoteStatus(s.value) for s in rsf.in_])
        if rsf.equals is not None:
            remote_statuses.append(DataArtifactRemoteStatus(rsf.equals.value))
        if remote_statuses:
            conditions.append(ArtifactRevisionConditions.by_remote_statuses(remote_statuses))
        return conditions

    @staticmethod
    def _convert_gql_revision_orders(
        orders: list[ArtifactRevisionGQLOrderByInputDTO],
    ) -> list[QueryOrder]:
        """Convert GQL revision order DTOs to query orders."""
        result: list[QueryOrder] = []
        for order in orders:
            ascending = order.direction == OrderDirection.ASC
            match order.field:
                case ArtifactRevisionOrderField.VERSION:
                    result.append(ArtifactRevisionOrders.version(ascending))
                case ArtifactRevisionOrderField.STATUS:
                    result.append(ArtifactRevisionOrders.status(ascending))
                case ArtifactRevisionOrderField.SIZE:
                    result.append(ArtifactRevisionOrders.size(ascending))
                case ArtifactRevisionOrderField.CREATED_AT:
                    result.append(ArtifactRevisionOrders.created_at(ascending))
                case ArtifactRevisionOrderField.UPDATED_AT:
                    result.append(ArtifactRevisionOrders.updated_at(ascending))
        return result

    def _convert_filter(self, filter: ArtifactFilter) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
        if filter.name is not None:
            condition = self.convert_string_filter(
                filter.name,
                contains_factory=ArtifactConditions.by_name_contains,
                equals_factory=ArtifactConditions.by_name_equals,
                starts_with_factory=ArtifactConditions.by_name_starts_with,
                ends_with_factory=ArtifactConditions.by_name_ends_with,
                in_factory=ArtifactConditions.by_name_in,
            )
            if condition is not None:
                conditions.append(condition)
        if filter.type is not None:
            conditions.extend(self._convert_type_filter(filter.type))
        if filter.availability is not None:
            conditions.extend(self._convert_availability_filter(filter.availability))
        return conditions

    @staticmethod
    def _convert_type_filter(tf: ArtifactTypeFilter) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
        if tf.equals is not None:
            conditions.append(ArtifactConditions.by_type_equals(DataArtifactType(tf.equals)))
        if tf.in_ is not None:
            conditions.append(ArtifactConditions.by_types([DataArtifactType(t) for t in tf.in_]))
        if tf.not_equals is not None:
            conditions.append(
                ArtifactConditions.by_type_not_equals(DataArtifactType(tf.not_equals))
            )
        if tf.not_in is not None:
            conditions.append(
                ArtifactConditions.by_types_not_in([DataArtifactType(t) for t in tf.not_in])
            )
        return conditions

    @staticmethod
    def _convert_availability_filter(
        af: ArtifactAvailabilityFilter,
    ) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
        if af.equals is not None:
            conditions.append(
                ArtifactConditions.by_availability_equals(DataArtifactAvailability(af.equals))
            )
        if af.in_ is not None:
            conditions.append(
                ArtifactConditions.by_availability([DataArtifactAvailability(a) for a in af.in_])
            )
        if af.not_equals is not None:
            conditions.append(
                ArtifactConditions.by_availability_not_equals(
                    DataArtifactAvailability(af.not_equals)
                )
            )
        if af.not_in is not None:
            conditions.append(
                ArtifactConditions.by_availability_not_in([
                    DataArtifactAvailability(a) for a in af.not_in
                ])
            )
        return conditions

    @staticmethod
    def _convert_orders(order: list[ArtifactOrder]) -> list[QueryOrder]:
        return [resolve_order(o.field, o.direction) for o in order]

    @staticmethod
    def _build_pagination(input: AdminSearchArtifactsInput) -> OffsetPagination:
        return OffsetPagination(
            limit=input.limit if input.limit is not None else DEFAULT_PAGINATION_LIMIT,
            offset=input.offset if input.offset is not None else 0,
        )

    @staticmethod
    def _build_gql_pagination_artifacts(
        input: AdminSearchArtifactsGQLInput,
    ) -> OffsetPagination:
        return OffsetPagination(
            limit=input.limit if input.limit is not None else DEFAULT_PAGINATION_LIMIT,
            offset=input.offset if input.offset is not None else 0,
        )

    @staticmethod
    def _build_gql_pagination_revisions(
        input: AdminSearchArtifactRevisionsInput,
    ) -> OffsetPagination:
        return OffsetPagination(
            limit=input.limit if input.limit is not None else DEFAULT_PAGINATION_LIMIT,
            offset=input.offset if input.offset is not None else 0,
        )

    @staticmethod
    def _data_to_dto(data: ArtifactData) -> ArtifactNode:
        return ArtifactNode(
            id=data.id,
            name=data.name,
            type=ArtifactType(data.type),
            description=data.description,
            registry_id=data.registry_id,
            source_registry_id=data.source_registry_id,
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
            artifact_id=data.artifact_id,
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
            name=data.name,
            type=ArtifactType(data.type),
            description=data.description,
            registry_id=data.registry_id,
            source_registry_id=data.source_registry_id,
            registry_type=data.registry_type,
            source_registry_type=data.source_registry_type,
            availability=ArtifactAvailability(data.availability),
            scanned_at=data.scanned_at,
            updated_at=data.updated_at,
            readonly=data.readonly,
            extra=data.extra,
            revisions=[ArtifactAdapter._revision_data_to_dto(r) for r in data.revisions],
        )
