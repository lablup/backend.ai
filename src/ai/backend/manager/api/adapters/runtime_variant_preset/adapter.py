from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from ai.backend.common.data.entity.runtime_variant import RuntimeVariantID
from ai.backend.common.data.entity.runtime_variant_preset import RuntimeVariantPresetID
from ai.backend.common.dto.manager.v2.runtime_variant_preset.request import (
    CreateRuntimeVariantPresetInput,
    RuntimeVariantPresetFilter,
    RuntimeVariantPresetOrder,
    SearchRuntimeVariantPresetsInput,
    UpdateRuntimeVariantPresetInput,
)
from ai.backend.common.dto.manager.v2.runtime_variant_preset.response import (
    CreateRuntimeVariantPresetPayload,
    DeleteRuntimeVariantPresetPayload,
    PresetTargetSpec,
    RuntimeVariantPresetNode,
    SearchRuntimeVariantPresetsPayload,
    UpdateRuntimeVariantPresetPayload,
)
from ai.backend.common.dto.manager.v2.runtime_variant_preset.types import (
    ChoiceItem,
    ChoiceOption,
    NumberOption,
    RuntimeVariantPresetOrderField,
    SliderOption,
    TextOption,
    UIOption,
    UIType,
)
from ai.backend.manager.api.adapter_options.pagination.pagination import PaginationSpec
from ai.backend.manager.api.adapters.base import BaseAdapter
from ai.backend.manager.data.runtime_variant_preset.types import (
    RuntimeVariantPresetData,
    UIOptionData,
)
from ai.backend.manager.models.clauses import QueryCondition, QueryOrder
from ai.backend.manager.models.condition_utils import combine_conditions_or, negate_conditions
from ai.backend.manager.models.runtime_variant_preset.creators import (
    RuntimeVariantPresetCreator,
)
from ai.backend.manager.models.runtime_variant_preset.row import RuntimeVariantPresetRow
from ai.backend.manager.models.runtime_variant_preset.scopes import (
    PublicRuntimeVariantPresetTarget,
)
from ai.backend.manager.models.runtime_variant_preset.searchable_fields import (
    RuntimeVariantPresetSearchableFields,
)
from ai.backend.manager.models.runtime_variant_preset.searchers import (
    RuntimeVariantPresetSearcher,
)
from ai.backend.manager.models.runtime_variant_preset.updaters import (
    RuntimeVariantPresetUpdater,
)
from ai.backend.manager.models.specs.searcher import ScopedSearcher
from ai.backend.manager.services.runtime_variant_preset.actions.bulk_get import (
    PublicBulkGetRuntimeVariantPresetsAction,
)
from ai.backend.manager.services.runtime_variant_preset.actions.create import (
    CreateRuntimeVariantPresetAction,
)
from ai.backend.manager.services.runtime_variant_preset.actions.get import (
    GetRuntimeVariantPresetAction,
)
from ai.backend.manager.services.runtime_variant_preset.actions.purge import (
    PurgeRuntimeVariantPresetAction,
)
from ai.backend.manager.services.runtime_variant_preset.actions.scoped_search import (
    ScopedSearchRuntimeVariantPresetsAction,
)
from ai.backend.manager.services.runtime_variant_preset.actions.update import (
    UpdateRuntimeVariantPresetAction,
)
from ai.backend.manager.services.runtime_variant_preset.processors import (
    RuntimeVariantPresetProcessors,
)
from ai.backend.manager.types import OptionalState, TriState


def _preset_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=RuntimeVariantPresetSearchableFields.own.created_at.order.apply(
            ascending=False
        ),
        cursor_column=RuntimeVariantPresetRow.id,
    )


def _convert_ui_option_data(opt: UIOptionData | None) -> UIOption | None:
    if opt is None:
        return None
    return UIOption(
        ui_type=UIType(opt.ui_type) if opt.ui_type else UIType.TEXT_INPUT,
        slider=SliderOption(min=opt.slider.min, max=opt.slider.max, step=opt.slider.step)
        if opt.slider
        else None,
        number=NumberOption(min=opt.number.min, max=opt.number.max) if opt.number else None,
        choices=ChoiceOption(
            items=[ChoiceItem(value=c.value, label=c.label) for c in opt.choices.items]
        )
        if opt.choices
        else None,
        text=TextOption(placeholder=opt.text.placeholder) if opt.text else None,
    )


class RuntimeVariantPresetAdapter(BaseAdapter):
    _runtime_variant_preset: RuntimeVariantPresetProcessors

    def __init__(self, runtime_variant_preset: RuntimeVariantPresetProcessors) -> None:
        self._runtime_variant_preset = runtime_variant_preset

    async def search(
        self,
        input: SearchRuntimeVariantPresetsInput,
    ) -> SearchRuntimeVariantPresetsPayload:
        conditions = self._convert_filter(input.filter) if input.filter else []
        orders = self._convert_orders(input.order) if input.order else []
        searcher = self._build_searcher(
            RuntimeVariantPresetSearcher,
            conditions=conditions,
            orders=orders,
            pagination_spec=_preset_pagination_spec(),
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )
        result = await self._runtime_variant_preset.scoped_search.run(self._scoped_search(searcher))
        return SearchRuntimeVariantPresetsPayload(
            items=[self._data_to_node(d) for d in result.items],
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def get(self, preset_id: UUID) -> RuntimeVariantPresetNode:
        result = await self._runtime_variant_preset.get.run(
            GetRuntimeVariantPresetAction(preset_id=RuntimeVariantPresetID(preset_id))
        )
        return self._data_to_node(result.data)

    async def batch_load_by_ids(
        self, ids: Sequence[RuntimeVariantPresetID]
    ) -> list[RuntimeVariantPresetNode | Exception | None]:
        """Batch load presets by id for DataLoader use.

        One answer per id in the given order: the node, or ``None`` for an id matching
        no row.
        """
        if not ids:
            return []
        result = await self._runtime_variant_preset.public_bulk_get.run(
            PublicBulkGetRuntimeVariantPresetsAction(ids=list(ids))
        )
        return [
            self._data_to_node(item.value)
            if item.value is not None
            else self.batch_load_failure(item.error)
            for item in result.items
        ]

    async def create(
        self,
        input: CreateRuntimeVariantPresetInput,
    ) -> CreateRuntimeVariantPresetPayload:
        creator = RuntimeVariantPresetCreator(
            runtime_variant_id=RuntimeVariantID(input.runtime_variant_id),
            name=input.name,
            description=input.description,
            preset_target=input.preset_target,
            value_type=input.value_type,
            default_value=input.default_value,
            key=input.key,
            required=input.required,
            added_version=input.added_version,
            deprecated_version=input.deprecated_version,
            category=input.category,
            display_name=input.display_name,
            ui_option=input.ui_option,
        )
        result = await self._runtime_variant_preset.global_create.run(
            CreateRuntimeVariantPresetAction(creator=creator)
        )
        return CreateRuntimeVariantPresetPayload(preset=self._data_to_node(result.data))

    async def update(
        self,
        input: UpdateRuntimeVariantPresetInput,
    ) -> UpdateRuntimeVariantPresetPayload:
        updater = RuntimeVariantPresetUpdater(
            preset_id=RuntimeVariantPresetID(input.id),
            name=OptionalState.from_unset(input.name),
            description=TriState.from_unset(input.description),
            rank=OptionalState.from_unset(input.rank),
            preset_target=OptionalState.from_unset(input.preset_target),
            value_type=OptionalState.from_unset(input.value_type),
            default_value=TriState.from_unset(input.default_value),
            key=OptionalState.from_unset(input.key),
            required=OptionalState.from_unset(input.required),
            added_version=TriState.from_unset(input.added_version),
            deprecated_version=TriState.from_unset(input.deprecated_version),
            category=TriState.from_unset(input.category),
            display_name=TriState.from_unset(input.display_name),
            ui_option=TriState.from_unset(input.ui_option),
        )
        result = await self._runtime_variant_preset.update.run(
            UpdateRuntimeVariantPresetAction(updater=updater)
        )
        return UpdateRuntimeVariantPresetPayload(preset=self._data_to_node(result.preset))

    async def delete(self, preset_id: UUID) -> DeleteRuntimeVariantPresetPayload:
        result = await self._runtime_variant_preset.purge.run(
            PurgeRuntimeVariantPresetAction(id=RuntimeVariantPresetID(preset_id))
        )
        return DeleteRuntimeVariantPresetPayload(id=result.data.id)

    def _scoped_search(
        self, searcher: RuntimeVariantPresetSearcher
    ) -> ScopedSearchRuntimeVariantPresetsAction:
        return ScopedSearchRuntimeVariantPresetsAction(
            searcher=ScopedSearcher(
                scopes=[PublicRuntimeVariantPresetTarget()], used_by=(), searcher=searcher
            )
        )

    def _convert_filter(self, filter_: RuntimeVariantPresetFilter) -> list[QueryCondition]:
        fields = RuntimeVariantPresetSearchableFields.own
        conditions: list[QueryCondition] = [
            *self.apply_uuid_filter(filter_.runtime_variant_id, fields.runtime_variant_id.filter),
            *self.apply_string_filter(filter_.name, fields.name.filter),
        ]
        if filter_.runtime_version is not None:
            conditions.extend(fields.valid_at_version(filter_.runtime_version))
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

    def _convert_orders(self, orders: list[RuntimeVariantPresetOrder]) -> list[QueryOrder]:
        fields = RuntimeVariantPresetSearchableFields.own
        result: list[QueryOrder] = []
        for order in orders:
            ascending = order.direction.value == "ASC"
            match order.field:
                case RuntimeVariantPresetOrderField.NAME:
                    result.append(fields.name.order.apply(ascending))
                case RuntimeVariantPresetOrderField.RANK:
                    result.append(fields.rank.order.apply(ascending))
                case RuntimeVariantPresetOrderField.CREATED_AT:
                    result.append(fields.created_at.order.apply(ascending))
                case RuntimeVariantPresetOrderField.ADDED_VERSION:
                    result.extend(fields.added_version_order(ascending))
                case RuntimeVariantPresetOrderField.DEPRECATED_VERSION:
                    result.extend(fields.deprecated_version_order(ascending))
        return result

    @staticmethod
    def _data_to_node(data: RuntimeVariantPresetData) -> RuntimeVariantPresetNode:
        return RuntimeVariantPresetNode(
            id=data.id,
            entity_id=data.entity_id(),
            runtime_variant_id=data.runtime_variant_id,
            name=data.name,
            description=data.description,
            rank=data.rank,
            target_spec=PresetTargetSpec(
                preset_target=data.preset_target,
                value_type=data.value_type,
                default_value=data.default_value,
                key=data.key,
            ),
            required=data.required,
            added_version=data.added_version,
            deprecated_version=data.deprecated_version,
            category=data.category,
            ui_type=data.ui_type,
            display_name=data.display_name,
            ui_option=_convert_ui_option_data(data.ui_option),
            created_at=data.created_at,
            updated_at=data.updated_at,
        )
