from __future__ import annotations

from uuid import UUID

from ai.backend.common.api_handlers import SENTINEL
from ai.backend.common.dto.manager.v2.model_card.request import (
    CreateModelCardInput,
    ModelCardFilter,
    ModelCardOrder,
    ResourceSlotEntryInput,
    SearchModelCardsInput,
    UpdateModelCardInput,
)
from ai.backend.common.dto.manager.v2.model_card.response import (
    CreateModelCardPayload,
    DeleteModelCardPayload,
    ModelCardMetadata,
    ModelCardNode,
    ResourceSlotEntryInfo,
    SearchModelCardsPayload,
    UpdateModelCardPayload,
)
from ai.backend.common.dto.manager.v2.model_card.types import ModelCardOrderField
from ai.backend.manager.api.adapters.pagination import PaginationSpec
from ai.backend.manager.data.model_card.types import ModelCardData
from ai.backend.manager.errors.resource import ModelCardNotFound
from ai.backend.manager.models.model_card.conditions import ModelCardConditions
from ai.backend.manager.models.model_card.orders import ModelCardOrders
from ai.backend.manager.models.model_card.row import ModelCardRow
from ai.backend.manager.models.model_card.types import MinResourceSpec
from ai.backend.manager.repositories.base import QueryCondition, QueryOrder, combine_conditions_or
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.model_card.creators import ModelCardCreatorSpec
from ai.backend.manager.repositories.model_card.updaters import ModelCardUpdaterSpec
from ai.backend.manager.services.model_card.actions.create import CreateModelCardAction
from ai.backend.manager.services.model_card.actions.delete import DeleteModelCardAction
from ai.backend.manager.services.model_card.actions.search import SearchModelCardsAction
from ai.backend.manager.services.model_card.actions.update import UpdateModelCardAction
from ai.backend.manager.types import OptionalState, TriState

from .base import BaseAdapter


def _model_card_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=ModelCardOrders.created_at(ascending=False),
        backward_order=ModelCardOrders.created_at(ascending=True),
        forward_condition_factory=ModelCardConditions.by_cursor_forward,
        backward_condition_factory=ModelCardConditions.by_cursor_backward,
        tiebreaker_order=ModelCardRow.id.asc(),
    )


def _entries_to_min_resource(entries: list[ResourceSlotEntryInput]) -> MinResourceSpec:
    return MinResourceSpec(slots={e.resource_type: e.quantity for e in entries})


def _min_resource_to_entries(slots: dict[str, str]) -> list[ResourceSlotEntryInfo]:
    return [ResourceSlotEntryInfo(resource_type=k, quantity=v) for k, v in slots.items()]


class ModelCardAdapter(BaseAdapter):
    async def search(
        self,
        input: SearchModelCardsInput,
    ) -> SearchModelCardsPayload:
        conditions = self._convert_filter(input.filter) if input.filter else []
        orders = self._convert_orders(input.order) if input.order else []
        querier = self._build_querier(
            conditions=conditions,
            orders=orders,
            pagination_spec=_model_card_pagination_spec(),
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )
        result = await self._processors.model_card.search.wait_for_complete(
            SearchModelCardsAction(querier=querier)
        )
        return SearchModelCardsPayload(
            items=[self._data_to_node(d) for d in result.items],
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def get(self, card_id: UUID) -> ModelCardNode:
        conditions: list[QueryCondition] = [lambda: ModelCardRow.id == card_id]
        querier = self._build_querier(
            conditions=conditions,
            orders=[],
            pagination_spec=_model_card_pagination_spec(),
            limit=1,
        )
        result = await self._processors.model_card.search.wait_for_complete(
            SearchModelCardsAction(querier=querier)
        )
        if not result.items:
            raise ModelCardNotFound()
        return self._data_to_node(result.items[0])

    async def create(
        self,
        input: CreateModelCardInput,
    ) -> CreateModelCardPayload:
        min_resource = _entries_to_min_resource(input.min_resource) if input.min_resource else None
        creator = Creator(
            spec=ModelCardCreatorSpec(
                name=input.name,
                vfolder_id=input.vfolder_id,
                domain=input.domain_name,
                project_id=input.project_id,
                creator_id=input.creator_id,
                author=input.author,
                title=input.title,
                model_version=input.model_version,
                description=input.description,
                task=input.task,
                category=input.category,
                architecture=input.architecture,
                framework=input.framework,
                label=input.label,
                license=input.license,
                min_resource=min_resource,
                readme=input.readme,
            )
        )
        result = await self._processors.model_card.create.wait_for_complete(
            CreateModelCardAction(creator=creator)
        )
        return CreateModelCardPayload(model_card=self._data_to_node(result.model_card))

    async def update(
        self,
        input: UpdateModelCardInput,
    ) -> UpdateModelCardPayload:
        min_resource_state: TriState[MinResourceSpec] = TriState.nop()
        if input.min_resource is not SENTINEL:
            if input.min_resource is None:
                min_resource_state = TriState.nullify()
            else:
                min_resource_state = TriState.update(_entries_to_min_resource(input.min_resource))

        spec = ModelCardUpdaterSpec(
            name=(
                OptionalState.update(input.name) if input.name is not None else OptionalState.nop()
            ),
            author=(
                TriState.nop()
                if input.author is SENTINEL
                else TriState.nullify()
                if input.author is None
                else TriState.update(input.author)
            ),
            title=(
                TriState.nop()
                if input.title is SENTINEL
                else TriState.nullify()
                if input.title is None
                else TriState.update(input.title)
            ),
            model_version=(
                TriState.nop()
                if input.model_version is SENTINEL
                else TriState.nullify()
                if input.model_version is None
                else TriState.update(input.model_version)
            ),
            description=(
                TriState.nop()
                if input.description is SENTINEL
                else TriState.nullify()
                if input.description is None
                else TriState.update(input.description)
            ),
            task=(
                TriState.nop()
                if input.task is SENTINEL
                else TriState.nullify()
                if input.task is None
                else TriState.update(input.task)
            ),
            category=(
                TriState.nop()
                if input.category is SENTINEL
                else TriState.nullify()
                if input.category is None
                else TriState.update(input.category)
            ),
            architecture=(
                TriState.nop()
                if input.architecture is SENTINEL
                else TriState.nullify()
                if input.architecture is None
                else TriState.update(input.architecture)
            ),
            framework=(
                OptionalState.update(input.framework)
                if input.framework is not None
                else OptionalState.nop()
            ),
            label=(
                OptionalState.update(input.label)
                if input.label is not None
                else OptionalState.nop()
            ),
            license=(
                TriState.nop()
                if input.license is SENTINEL
                else TriState.nullify()
                if input.license is None
                else TriState.update(input.license)
            ),
            min_resource=min_resource_state,
            readme=(
                TriState.nop()
                if input.readme is SENTINEL
                else TriState.nullify()
                if input.readme is None
                else TriState.update(input.readme)
            ),
        )
        updater: Updater[ModelCardRow] = Updater(spec=spec, pk_value=input.id)
        result = await self._processors.model_card.update.wait_for_complete(
            UpdateModelCardAction(id=input.id, updater=updater)
        )
        return UpdateModelCardPayload(model_card=self._data_to_node(result.model_card))

    async def delete(self, card_id: UUID) -> DeleteModelCardPayload:
        result = await self._processors.model_card.delete.wait_for_complete(
            DeleteModelCardAction(id=card_id)
        )
        return DeleteModelCardPayload(id=result.model_card.id)

    def _convert_filter(self, filter_: ModelCardFilter) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
        if filter_.domain_name is not None:
            conditions.append(ModelCardConditions.by_domain(filter_.domain_name))
        if filter_.project_id is not None:
            conditions.append(ModelCardConditions.by_project(filter_.project_id))
        if filter_.name:
            cond = self.convert_string_filter(
                filter_.name,
                contains_factory=ModelCardConditions.by_name_contains,
                equals_factory=ModelCardConditions.by_name_equals,
                starts_with_factory=ModelCardConditions.by_name_starts_with,
                ends_with_factory=ModelCardConditions.by_name_ends_with,
            )
            if cond:
                conditions.append(cond)
        if filter_.AND:
            for sub in filter_.AND:
                conditions.extend(self._convert_filter(sub))
        if filter_.OR:
            or_conds: list[QueryCondition] = []
            for sub in filter_.OR:
                or_conds.extend(self._convert_filter(sub))
            if or_conds:
                conditions.append(combine_conditions_or(or_conds))
        return conditions

    def _convert_orders(self, orders: list[ModelCardOrder]) -> list[QueryOrder]:
        result: list[QueryOrder] = []
        for order in orders:
            ascending = order.direction.value == "ASC"
            match order.field:
                case ModelCardOrderField.NAME:
                    result.append(ModelCardOrders.name(ascending))
                case ModelCardOrderField.CREATED_AT:
                    result.append(ModelCardOrders.created_at(ascending))
        return result

    @staticmethod
    def _data_to_node(data: ModelCardData) -> ModelCardNode:
        return ModelCardNode(
            id=data.id,
            name=data.name,
            vfolder_id=data.vfolder_id,
            domain_name=data.domain,
            project_id=data.project_id,
            creator_id=data.creator_id,
            metadata=ModelCardMetadata(
                author=data.author,
                title=data.title,
                model_version=data.model_version,
                description=data.description,
                task=data.task,
                category=data.category,
                architecture=data.architecture,
                framework=data.framework,
                label=data.label,
                license=data.license,
            ),
            min_resource=(
                _min_resource_to_entries(data.min_resource) if data.min_resource else None
            ),
            readme=data.readme,
            created_at=data.created_at,
            updated_at=data.updated_at,
        )
