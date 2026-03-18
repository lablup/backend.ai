"""Artifact adapter bridging DTOs and Processors."""

from __future__ import annotations

from uuid import UUID

from ai.backend.common.api_handlers import Sentinel
from ai.backend.common.dto.manager.v2.artifact.request import (
    AdminSearchArtifactsInput,
    ArtifactFilter,
    ArtifactOrder,
    DeleteArtifactsInput,
    UpdateArtifactInput,
)
from ai.backend.common.dto.manager.v2.artifact.response import (
    AdminSearchArtifactsPayload,
    ArtifactNode,
    DeleteArtifactsPayload,
    UpdateArtifactPayload,
)
from ai.backend.common.dto.manager.v2.artifact.types import (
    ArtifactAvailability,
    ArtifactAvailabilityFilter,
    ArtifactType,
    ArtifactTypeFilter,
)
from ai.backend.manager.data.artifact.types import (
    ArtifactAvailability as DataArtifactAvailability,
)
from ai.backend.manager.data.artifact.types import (
    ArtifactData,
)
from ai.backend.manager.data.artifact.types import (
    ArtifactType as DataArtifactType,
)
from ai.backend.manager.models.artifact.conditions import ArtifactConditions
from ai.backend.manager.models.artifact.orders import (
    DEFAULT_FORWARD_ORDER,
    TIEBREAKER_ORDER,
    resolve_order,
)
from ai.backend.manager.models.artifact.row import ArtifactRow
from ai.backend.manager.repositories.artifact.updaters import ArtifactUpdaterSpec
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    OffsetPagination,
    QueryCondition,
    QueryOrder,
)
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.services.artifact.actions.delete_multi import DeleteArtifactsAction
from ai.backend.manager.services.artifact.actions.get import GetArtifactAction
from ai.backend.manager.services.artifact.actions.search import SearchArtifactsAction
from ai.backend.manager.services.artifact.actions.update import UpdateArtifactAction
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

    def build_querier(self, input: AdminSearchArtifactsInput) -> BatchQuerier:
        """Build a BatchQuerier from the search input DTO."""
        conditions = self._convert_filter(input.filter) if input.filter else []
        orders = self._convert_orders(input.order) if input.order else [DEFAULT_FORWARD_ORDER]
        orders.append(TIEBREAKER_ORDER)
        pagination = self._build_pagination(input)
        return BatchQuerier(conditions=conditions, orders=orders, pagination=pagination)

    def _convert_filter(self, filter: ArtifactFilter) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
        if filter.name is not None:
            condition = self.convert_string_filter(
                filter.name,
                contains_factory=ArtifactConditions.by_name_contains,
                equals_factory=ArtifactConditions.by_name_equals,
                starts_with_factory=ArtifactConditions.by_name_starts_with,
                ends_with_factory=ArtifactConditions.by_name_ends_with,
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
