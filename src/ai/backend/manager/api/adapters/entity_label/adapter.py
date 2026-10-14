"""Label adapter bridging DTOs and Processors."""

from __future__ import annotations

from collections.abc import Sequence

from ai.backend.common.data.entity.entity_label import EntityLabelID, EntityLabelKey
from ai.backend.common.data.entity.types import RuntimeEntityID
from ai.backend.common.dto.manager.v2.entity.types import EntityTarget
from ai.backend.common.dto.manager.v2.entity_label.request import (
    EntityLabelOrder,
    EntityLabelPageInput,
    PartialBulkPurgeEntityLabelInput,
    PartialBulkUpsertEntityLabelInput,
    SearchEntityLabelsInput,
    UpsertEntityLabelInput,
)
from ai.backend.common.dto.manager.v2.entity_label.response import (
    EntityLabelNode,
    PartialBulkPurgeEntityLabelPayload,
    PartialBulkUpsertEntityLabelPayload,
    PurgeEntityLabelError,
    PurgeEntityLabelPayload,
    SearchEntityLabelsPayload,
    UpsertEntityLabelError,
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
from ai.backend.manager.errors.base.field import FieldNotFoundError
from ai.backend.manager.models.clauses import QueryOrder
from ai.backend.manager.models.entity_label.row import EntityLabelRow
from ai.backend.manager.models.entity_label.searchable_fields import EntityLabelSearchableFields
from ai.backend.manager.models.entity_label.searchers import EntityLabelSearcher
from ai.backend.manager.models.entity_label.upserters import EntityLabelUpserter
from ai.backend.manager.services.entity_label.actions.partial_bulk_get import (
    PartialBulkGetEntityLabelAction,
)
from ai.backend.manager.services.entity_label.actions.partial_bulk_purge import (
    PartialBulkPurgeEntityLabelAction,
)
from ai.backend.manager.services.entity_label.actions.partial_bulk_upsert import (
    EntityLabelToUpsert,
    PartialBulkUpsertEntityLabelAction,
)
from ai.backend.manager.services.entity_label.actions.purge import PurgeEntityLabelAction
from ai.backend.manager.services.entity_label.actions.search import SearchEntityLabelsAction
from ai.backend.manager.services.entity_label.actions.upsert import UpsertEntityLabelAction
from ai.backend.manager.services.entity_label.processors import EntityLabelProcessors

_LABEL_PAGINATION_SPEC = PaginationSpec(
    forward_order=EntityLabelSearchableFields.own.created_at.order.apply(ascending=False),
    cursor_column=EntityLabelRow.id,
)


class EntityLabelAdapter(BaseAdapter):
    """Adapter for label domain operations."""

    _entity_label: EntityLabelProcessors
    _entity_types: WiredEntityTypes

    def __init__(self, entity_label: EntityLabelProcessors, entity_types: WiredEntityTypes) -> None:
        self._entity_label = entity_label
        self._entity_types = entity_types

    async def upsert(self, input: UpsertEntityLabelInput) -> UpsertEntityLabelPayload:
        """Set one key on the entity the request names, replacing the value it carries."""
        action_result = await self._entity_label.upsert.run(
            UpsertEntityLabelAction(
                owner=self._target(input.target),
                upserter=EntityLabelUpserter(key=EntityLabelKey(input.key), value=input.value),
            )
        )
        return UpsertEntityLabelPayload(label=self._data_to_node(action_result.data))

    async def partial_bulk_upsert(
        self, input: PartialBulkUpsertEntityLabelInput
    ) -> PartialBulkUpsertEntityLabelPayload:
        """Set keys on the entities the request names, answered per request item; an
        entity's items share one fate, and a type nothing is wired for refuses the
        whole request."""
        items = [
            EntityLabelToUpsert(
                owner=self._target(item.target),
                upserter=EntityLabelUpserter(key=EntityLabelKey(item.key), value=item.value),
            )
            for item in input.items
        ]
        action_result = await self._entity_label.partial_bulk_upsert.run(
            PartialBulkUpsertEntityLabelAction(items=items)
        )
        errors = action_result.errors()
        return PartialBulkUpsertEntityLabelPayload(
            items=[
                self._data_to_node(data)
                for answer in action_result.items
                if answer.value is not None
                for data in answer.value
            ],
            failed=[
                UpsertEntityLabelError(
                    entity_type=item.owner.entity_type(),
                    entity_id=item.owner,
                    key=item.upserter.key,
                    message=str(errors[item.owner]),
                )
                for item in items
                if item.owner in errors
            ],
        )

    async def purge(self, label_id: EntityLabelID) -> PurgeEntityLabelPayload:
        """Take one label off, named by its own id.

        Which entity answers for it is read from the row before the delete runs, so a
        caller reaching for a label on an entity they cannot see is refused there.
        """
        action_result = await self._entity_label.purge.run(
            PurgeEntityLabelAction(label_id=label_id)
        )
        return PurgeEntityLabelPayload(label=self._data_to_node(action_result.data))

    async def partial_bulk_purge(
        self, input: PartialBulkPurgeEntityLabelInput
    ) -> PartialBulkPurgeEntityLabelPayload:
        """Take several labels off by id, answered per id. A run every id of which names
        no row is refused below and folded back into one failed item per id here, so
        the caller reads one shape whatever it named."""
        label_ids = list(dict.fromkeys(EntityLabelID(one) for one in input.ids))
        try:
            action_result = await self._entity_label.partial_bulk_purge.run(
                PartialBulkPurgeEntityLabelAction(label_ids=label_ids)
            )
        except FieldNotFoundError as e:
            return PartialBulkPurgeEntityLabelPayload(
                successes=[],
                failed=[
                    PurgeEntityLabelError(id=label_id, message=str(e)) for label_id in label_ids
                ],
            )
        return PartialBulkPurgeEntityLabelPayload(
            successes=[label_id for label_id in label_ids if label_id in action_result.successes],
            failed=[
                PurgeEntityLabelError(id=label_id, message=str(action_result.errors[label_id]))
                for label_id in label_ids
                if label_id in action_result.errors
            ],
        )

    async def batch_load_by_ids(
        self, ids: Sequence[EntityLabelID]
    ) -> list[EntityLabelNode | Exception | None]:
        """Batch load labels for DataLoader use, checked per labeled entity."""
        if not ids:
            return []
        return await self.batch_load_fields(
            self._entity_label.partial_bulk_get,
            PartialBulkGetEntityLabelAction(label_ids=ids),
            ids,
            self._data_to_node,
        )

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
        action_result = await self._entity_label.search.run(
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

    def _convert_orders(self, orders: list[EntityLabelOrder]) -> list[QueryOrder]:
        return [self._convert_order(order) for order in orders]

    def _convert_order(self, order: EntityLabelOrder) -> QueryOrder:
        fields = EntityLabelSearchableFields.own
        ascending = order.direction == OrderDirection.ASC
        match order.field:
            case EntityLabelOrderField.KEY:
                return fields.key.order.apply(ascending)
            case EntityLabelOrderField.VALUE:
                return fields.value.order.apply(ascending)
            case EntityLabelOrderField.CREATED_AT:
                return fields.created_at.order.apply(ascending)

    @staticmethod
    def _data_to_node(data: EntityLabelData) -> EntityLabelNode:
        return EntityLabelNode(
            id=data.id,
            field_id=data.id,
            entity_type=data.entity.entity_type(),
            entity_id=data.entity,
            key=data.key,
            value=data.value,
            created_at=data.created_at,
            updated_at=data.updated_at,
        )


__all__ = ("EntityLabelAdapter",)
