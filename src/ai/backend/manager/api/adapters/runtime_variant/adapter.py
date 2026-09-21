from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.entity.runtime_variant import RuntimeVariantID
from ai.backend.common.dto.manager.v2.runtime_variant.request import (
    CreateRuntimeVariantInput,
    DeleteRuntimeVariantsInput,
    RuntimeVariantFilter,
    RuntimeVariantOrder,
    SearchRuntimeVariantsInput,
    UpdateRuntimeVariantInput,
)
from ai.backend.common.dto.manager.v2.runtime_variant.response import (
    CreateRuntimeVariantPayload,
    DeleteRuntimeVariantPayload,
    DeleteRuntimeVariantsPayload,
    RuntimeVariantBulkFailureInfo,
    RuntimeVariantModelDefinitionInfo,
    RuntimeVariantNode,
    SearchRuntimeVariantsPayload,
    UpdateRuntimeVariantPayload,
)
from ai.backend.common.dto.manager.v2.runtime_variant.types import (
    RuntimeVariantOrderField,
    RuntimeVariantUsedBy,
)
from ai.backend.manager.api.adapter_options.pagination.pagination import PaginationSpec
from ai.backend.manager.api.adapters.base import BaseAdapter
from ai.backend.manager.data.runtime_variant.types import RuntimeVariantData
from ai.backend.manager.models.clauses import QueryCondition, QueryOrder
from ai.backend.manager.models.condition_utils import combine_conditions_or, negate_conditions
from ai.backend.manager.models.runtime_variant.creators import RuntimeVariantCreator
from ai.backend.manager.models.runtime_variant.row import RuntimeVariantRow
from ai.backend.manager.models.runtime_variant.scopes import PublicRuntimeVariantTarget
from ai.backend.manager.models.runtime_variant.searchable_fields import (
    RuntimeVariantSearchableFields,
)
from ai.backend.manager.models.runtime_variant.searchers import RuntimeVariantSearcher
from ai.backend.manager.models.runtime_variant.updaters import RuntimeVariantUpdater
from ai.backend.manager.models.specs.search.usage import UsedBy
from ai.backend.manager.models.specs.searcher import ScopedSearcher
from ai.backend.manager.services.runtime_variant.actions.bulk_get import (
    BulkGetRuntimeVariantsAction,
)
from ai.backend.manager.services.runtime_variant.actions.bulk_purge import (
    BulkPurgeRuntimeVariantsAction,
)
from ai.backend.manager.services.runtime_variant.actions.create import CreateRuntimeVariantAction
from ai.backend.manager.services.runtime_variant.actions.get import GetRuntimeVariantAction
from ai.backend.manager.services.runtime_variant.actions.lookup import (
    LookupRuntimeVariantAction,
)
from ai.backend.manager.services.runtime_variant.actions.purge import PurgeRuntimeVariantAction
from ai.backend.manager.services.runtime_variant.actions.scoped_search import (
    ScopedSearchRuntimeVariantsAction,
)
from ai.backend.manager.services.runtime_variant.actions.update import UpdateRuntimeVariantAction
from ai.backend.manager.services.runtime_variant.processors import RuntimeVariantProcessors
from ai.backend.manager.types import OptionalState, TriState


def _runtime_variant_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=RuntimeVariantSearchableFields.own.created_at.order.apply(ascending=False),
        cursor_column=RuntimeVariantRow.id,
    )


class RuntimeVariantAdapter(BaseAdapter):
    _runtime_variant: RuntimeVariantProcessors

    def __init__(self, runtime_variant: RuntimeVariantProcessors) -> None:
        self._runtime_variant = runtime_variant

    async def batch_load_by_ids(
        self, ids: Sequence[RuntimeVariantID]
    ) -> list[RuntimeVariantNode | Exception | None]:
        """Batch load runtime variants by id for DataLoader use.

        One answer per id in the given order: the node, ``None`` for an id matching no
        row, and the denial for one the caller may not read.
        """
        if not ids:
            return []
        entity_ids = [RuntimeVariantID(value) for value in ids]
        result = await self._runtime_variant.bulk_get.run(
            BulkGetRuntimeVariantsAction(ids=entity_ids)
        )
        return [
            self._data_to_node(item.value)
            if item.value is not None
            else self.batch_load_failure(item.error)
            for item in result.items
        ]

    async def search(
        self,
        input: SearchRuntimeVariantsInput,
    ) -> SearchRuntimeVariantsPayload:
        conditions = self._convert_filter(input.filter) if input.filter else []
        orders = self._convert_orders(input.order) if input.order else []
        searcher = self._build_searcher(
            RuntimeVariantSearcher,
            conditions=conditions,
            orders=orders,
            pagination_spec=_runtime_variant_pagination_spec(),
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )
        result = await self._runtime_variant.scoped_search.run(
            ScopedSearchRuntimeVariantsAction(
                searcher=ScopedSearcher(
                    scopes=[PublicRuntimeVariantTarget()],
                    used_by=self._used_by(input.used_by),
                    searcher=searcher,
                )
            )
        )
        return SearchRuntimeVariantsPayload(
            items=[self._data_to_node(d) for d in result.items],
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def get(self, variant_id: UUID) -> RuntimeVariantNode:
        result = await self._runtime_variant.get.run(
            GetRuntimeVariantAction(variant_id=RuntimeVariantID(variant_id))
        )
        return self._data_to_node(result.data)

    async def create(
        self,
        input: CreateRuntimeVariantInput,
    ) -> CreateRuntimeVariantPayload:
        creator = RuntimeVariantCreator(
            name=input.name,
            description=input.description,
        )
        result = await self._runtime_variant.global_create.run(
            CreateRuntimeVariantAction(creator=creator)
        )
        return CreateRuntimeVariantPayload(
            runtime_variant=self._data_to_node(result.data),
        )

    async def update(
        self,
        input: UpdateRuntimeVariantInput,
    ) -> UpdateRuntimeVariantPayload:
        updater = RuntimeVariantUpdater(
            variant_id=RuntimeVariantID(input.id),
            name=OptionalState.from_unset(input.name),
            description=TriState.from_unset(input.description),
        )
        result = await self._runtime_variant.update.run(UpdateRuntimeVariantAction(updater=updater))
        return UpdateRuntimeVariantPayload(
            runtime_variant=self._data_to_node(result.data),
        )

    async def delete(self, variant_id: UUID) -> DeleteRuntimeVariantPayload:
        result = await self._runtime_variant.purge.run(
            PurgeRuntimeVariantAction(id=RuntimeVariantID(variant_id))
        )
        return DeleteRuntimeVariantPayload(id=result.data.id)

    async def bulk_delete(self, input: DeleteRuntimeVariantsInput) -> DeleteRuntimeVariantsPayload:
        """Delete the named runtime variants, answering for each one."""
        result = await self._runtime_variant.bulk_purge.run(
            BulkPurgeRuntimeVariantsAction(
                ids=[RuntimeVariantID(variant_id) for variant_id in input.ids]
            )
        )
        items = [item.value.id for item in result.items if item.value is not None]
        return DeleteRuntimeVariantsPayload(
            items=items,
            failed=[
                RuntimeVariantBulkFailureInfo(
                    id=RuntimeVariantID(item.entity_id), message=str(item.error)
                )
                for item in result.items
                if item.error is not None
            ],
            deleted_count=len(items),
        )

    async def resolve_by_name(self, name: str) -> RuntimeVariantID:
        """Resolve a variant name into its ``RuntimeVariantID``.

        Sole entry point used by legacy API handlers to upgrade name-
        carrying inputs before calling id-typed internal adapters. Does
        not form part of the v2 surface — v2 clients pass the id
        directly.
        """
        result = await self._runtime_variant.lookup.run(LookupRuntimeVariantAction(name=name))
        return result.entity_id()

    def _used_by(self, used_by: RuntimeVariantUsedBy | None) -> list[UsedBy]:
        """The uses the request named, each of which the caller must be able to read."""
        if used_by is None:
            return []
        linked = RuntimeVariantSearchableFields.linked
        return [
            linked.deployments.used_by(DeploymentID(entity_id))
            for entity_id in used_by.deployment or ()
        ]

    def _convert_filter(self, filter_: RuntimeVariantFilter) -> list[QueryCondition]:
        fields = RuntimeVariantSearchableFields.own
        conditions: list[QueryCondition] = [
            *self.apply_string_filter(filter_.name, fields.name.filter),
        ]
        if filter_.AND:
            for sub in filter_.AND:
                conditions.extend(self._convert_filter(sub))
        if filter_.OR:
            or_conds: list[QueryCondition] = []
            for sub in filter_.OR:
                or_conds.extend(self._convert_filter(sub))
            if or_conds:
                conditions.append(combine_conditions_or(or_conds))
        if filter_.NOT:
            not_conds: list[QueryCondition] = []
            for sub in filter_.NOT:
                not_conds.extend(self._convert_filter(sub))
            if not_conds:
                conditions.append(negate_conditions(not_conds))
        return conditions

    def _convert_orders(self, orders: list[RuntimeVariantOrder]) -> list[QueryOrder]:
        fields = RuntimeVariantSearchableFields.own
        result = []
        for order in orders:
            ascending = order.direction.value == "ASC"
            match order.field:
                case RuntimeVariantOrderField.NAME:
                    result.append(fields.name.order.apply(ascending))
                case RuntimeVariantOrderField.CREATED_AT:
                    result.append(fields.created_at.order.apply(ascending))
        return result

    @staticmethod
    def _data_to_node(data: RuntimeVariantData) -> RuntimeVariantNode:
        return RuntimeVariantNode(
            id=data.id,
            entity_id=data.entity_id(),
            name=data.name,
            description=data.description,
            reads_vfolder_config_files=data.reads_vfolder_config_files,
            default_model_definition=RuntimeVariantModelDefinitionInfo.model_validate(
                data.default_model_definition,
                from_attributes=True,
            ),
            created_at=data.created_at,
            updated_at=data.updated_at,
        )
