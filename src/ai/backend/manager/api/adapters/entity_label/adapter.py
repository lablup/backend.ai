"""Label adapter bridging DTOs and Processors."""

from __future__ import annotations

from ai.backend.common.data.entity.entity_label import EntityLabelID, EntityLabelKey
from ai.backend.common.data.entity.types import RuntimeEntityID
from ai.backend.common.dto.manager.v2.entity.types import EntityTarget
from ai.backend.common.dto.manager.v2.entity_label.request import (
    EntityLabelOrder,
    EntityLabelPageInput,
    SearchEntityLabelsInput,
    UpsertEntityLabelInput,
)
from ai.backend.common.dto.manager.v2.entity_label.response import (
    EntityLabelNode,
    PurgeEntityLabelPayload,
    SearchEntityLabelsPayload,
    UpsertEntityLabelPayload,
)
from ai.backend.common.dto.manager.v2.entity_label.types import (
    EntityLabelOrderField,
    OrderDirection,
)
from ai.backend.manager.api.adapter_options.pagination.pagination import PaginationSpec
from ai.backend.manager.api.adapters.base import BaseAdapter
from ai.backend.manager.api.adapters.entity.types import WiredEntityTypes
from ai.backend.manager.data.entity_label.types import EntityLabelData
from ai.backend.manager.models.clauses import QueryOrder
from ai.backend.manager.models.entity_label.conditions import (
    EntityLabelConditions,
    EntityLabelOrders,
)
from ai.backend.manager.models.entity_label.row import EntityLabelRow
from ai.backend.manager.models.entity_label.searchers import EntityLabelSearcher
from ai.backend.manager.models.entity_label.upserters import EntityLabelUpserter
from ai.backend.manager.services.entity_label.actions.purge import PurgeEntityLabelAction
from ai.backend.manager.services.entity_label.actions.search import SearchEntityLabelsAction
from ai.backend.manager.services.entity_label.actions.upsert import UpsertEntityLabelAction
from ai.backend.manager.services.processors import Processors

_LABEL_PAGINATION_SPEC = PaginationSpec(
    forward_order=EntityLabelOrders.created_at(ascending=False),
    backward_order=EntityLabelOrders.created_at(ascending=True),
    forward_condition_factory=EntityLabelConditions.by_cursor_forward,
    backward_condition_factory=EntityLabelConditions.by_cursor_backward,
    tiebreaker_order=EntityLabelRow.id.asc(),
)


class EntityLabelAdapter(BaseAdapter):
    """Adapter for label domain operations."""

    _entity_types: WiredEntityTypes

    def __init__(self, processors: Processors, entity_types: WiredEntityTypes) -> None:
        super().__init__(processors)
        self._entity_types = entity_types

    async def upsert(self, input: UpsertEntityLabelInput) -> UpsertEntityLabelPayload:
        """Set one key on the entity the request names, replacing the value it carries."""
        action_result = await self._processors.entity_label.upsert.run(
            UpsertEntityLabelAction(
                owner=self._target(input.target),
                upserter=EntityLabelUpserter(key=EntityLabelKey(input.key), value=input.value),
            )
        )
        return UpsertEntityLabelPayload(label=self._data_to_node(action_result.data))

    async def purge(self, label_id: EntityLabelID) -> PurgeEntityLabelPayload:
        """Take one label off, named by its own id.

        Which entity answers for it is read from the row before the delete runs, so a
        caller reaching for a label on an entity they cannot see is refused there.
        """
        action_result = await self._processors.entity_label.purge.run(
            PurgeEntityLabelAction(label_id=label_id)
        )
        return PurgeEntityLabelPayload(label=self._data_to_node(action_result.data))

    async def search(self, input: SearchEntityLabelsInput) -> SearchEntityLabelsPayload:
        """Read a page of the labels on the entities named, OR'd across them and
        restricted to the ones the caller is RBAC-authorized for."""
        return await self._search([self._target(scope) for scope in input.scope], input)

    async def search_on(
        self, owner: RuntimeEntityID, input: EntityLabelPageInput
    ) -> SearchEntityLabelsPayload:
        """Read a page of the labels on one entity the caller already holds, so the
        entity names itself rather than being named again as a scope."""
        return await self._search([owner], input)

    async def _search(
        self, owners: list[RuntimeEntityID], input: EntityLabelPageInput
    ) -> SearchEntityLabelsPayload:
        conditions = self._convert_entity_label_filter(input.filter) if input.filter else []
        orders = self._convert_orders(input.order) if input.order else []
        searcher = self._build_searcher(
            EntityLabelSearcher,
            conditions=conditions,
            orders=orders,
            pagination_spec=_LABEL_PAGINATION_SPEC,
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )
        action_result = await self._processors.entity_label.search.run(
            SearchEntityLabelsAction(owners=owners, searcher=searcher)
        )
        return SearchEntityLabelsPayload(
            items=[self._data_to_node(item) for item in action_result.items],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    def _target(self, target: EntityTarget) -> RuntimeEntityID:
        """The entity the request names; a type nothing is wired for is refused here."""
        return RuntimeEntityID(self._entity_types.resolve(target.entity_type), target.entity_id)

    @staticmethod
    def _convert_orders(orders: list[EntityLabelOrder]) -> list[QueryOrder]:
        result: list[QueryOrder] = []
        for o in orders:
            ascending = o.direction == OrderDirection.ASC
            match o.field:
                case EntityLabelOrderField.KEY:
                    result.append(EntityLabelOrders.key(ascending))
                case EntityLabelOrderField.VALUE:
                    result.append(EntityLabelOrders.value(ascending))
                case EntityLabelOrderField.CREATED_AT:
                    result.append(EntityLabelOrders.created_at(ascending))
        return result

    @staticmethod
    def _data_to_node(data: EntityLabelData) -> EntityLabelNode:
        return EntityLabelNode(
            id=data.id,
            entity_type=data.entity.entity_type(),
            entity_id=data.entity,
            key=data.key,
            value=data.value,
            created_at=data.created_at,
            updated_at=data.updated_at,
        )


__all__ = ("EntityLabelAdapter",)
