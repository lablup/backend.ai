from __future__ import annotations

from typing import Any
from uuid import UUID

from ai.backend.common.api_handlers import SENTINEL
from ai.backend.common.config import ModelDefinition
from ai.backend.common.dto.manager.v2.deployment_revision_preset.request import (
    CreateDeploymentRevisionPresetInput,
    DeploymentRevisionPresetFilter,
    DeploymentRevisionPresetOrder,
    SearchDeploymentRevisionPresetsInput,
    UpdateDeploymentRevisionPresetInput,
)
from ai.backend.common.dto.manager.v2.deployment_revision_preset.response import (
    CreateDeploymentRevisionPresetPayload,
    DeleteDeploymentRevisionPresetPayload,
    DeploymentRevisionPresetNode,
    EnvironEntryInfo,
    PresetClusterSpec,
    PresetExecutionSpec,
    PresetResourceAllocation,
    PresetValueInfo,
    ResourceOptsEntryInfo,
    ResourceSlotEntryInfo,
    SearchDeploymentRevisionPresetsPayload,
    UpdateDeploymentRevisionPresetPayload,
)
from ai.backend.common.dto.manager.v2.deployment_revision_preset.types import (
    DeploymentRevisionPresetOrderField,
)
from ai.backend.manager.api.adapters.pagination import PaginationSpec
from ai.backend.manager.data.deployment_revision_preset.types import DeploymentRevisionPresetData
from ai.backend.manager.errors.resource import DeploymentRevisionPresetNotFound
from ai.backend.manager.models.base import ResourceOptsEntry, ResourceSlotEntry
from ai.backend.manager.models.deployment_revision_preset.conditions import (
    DeploymentRevisionPresetConditions,
)
from ai.backend.manager.models.deployment_revision_preset.orders import (
    DeploymentRevisionPresetOrders,
)
from ai.backend.manager.models.deployment_revision_preset.row import DeploymentRevisionPresetRow
from ai.backend.manager.models.deployment_revision_preset.types import PresetValueEntry
from ai.backend.manager.repositories.base import QueryCondition, QueryOrder, combine_conditions_or
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.deployment_revision_preset.creators import (
    DeploymentRevisionPresetCreatorSpec,
)
from ai.backend.manager.repositories.deployment_revision_preset.updaters import (
    DeploymentRevisionPresetUpdaterSpec,
)
from ai.backend.manager.services.deployment_revision_preset.actions.create import (
    CreateDeploymentRevisionPresetAction,
)
from ai.backend.manager.services.deployment_revision_preset.actions.delete import (
    DeleteDeploymentRevisionPresetAction,
)
from ai.backend.manager.services.deployment_revision_preset.actions.search import (
    SearchDeploymentRevisionPresetsAction,
)
from ai.backend.manager.services.deployment_revision_preset.actions.update import (
    UpdateDeploymentRevisionPresetAction,
)
from ai.backend.manager.types import OptionalState, TriState

from .base import BaseAdapter


def _preset_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=DeploymentRevisionPresetOrders.rank(ascending=True),
        backward_order=DeploymentRevisionPresetOrders.rank(ascending=False),
        forward_condition_factory=DeploymentRevisionPresetConditions.by_cursor_forward,
        backward_condition_factory=DeploymentRevisionPresetConditions.by_cursor_backward,
        tiebreaker_order=DeploymentRevisionPresetRow.id.asc(),
    )


class DeploymentRevisionPresetAdapter(BaseAdapter):
    async def search(
        self,
        input: SearchDeploymentRevisionPresetsInput,
    ) -> SearchDeploymentRevisionPresetsPayload:
        conditions = self._convert_filter(input.filter) if input.filter else []
        orders = self._convert_orders(input.order) if input.order else []
        querier = self._build_querier(
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
        result = await self._processors.deployment_revision_preset.search.wait_for_complete(
            SearchDeploymentRevisionPresetsAction(querier=querier)
        )
        return SearchDeploymentRevisionPresetsPayload(
            items=[self._data_to_node(d) for d in result.items],
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def get(self, preset_id: UUID) -> DeploymentRevisionPresetNode:
        conditions: list[QueryCondition] = [lambda: DeploymentRevisionPresetRow.id == preset_id]
        querier = self._build_querier(
            conditions=conditions,
            orders=[],
            pagination_spec=_preset_pagination_spec(),
            limit=1,
        )
        result = await self._processors.deployment_revision_preset.search.wait_for_complete(
            SearchDeploymentRevisionPresetsAction(querier=querier)
        )
        if not result.items:
            raise DeploymentRevisionPresetNotFound()
        return self._data_to_node(result.items[0])

    async def create(
        self,
        input: CreateDeploymentRevisionPresetInput,
    ) -> CreateDeploymentRevisionPresetPayload:
        resource_slots = self._convert_resource_slots_input(input.resource_slots)
        resource_opts = self._convert_resource_opts_input(input.resource_opts)
        environ = self._convert_environ_input(input.environ)
        preset_values = self._convert_preset_values_input(input.preset_values)
        model_def = ModelDefinition(**input.model_definition) if input.model_definition else None

        creator = Creator(
            spec=DeploymentRevisionPresetCreatorSpec(
                runtime_variant_id=input.runtime_variant_id,
                name=input.name,
                description=input.description,
                rank=0,
                image=input.image,
                model_definition=model_def,
                resource_slots=resource_slots,
                resource_opts=resource_opts,
                cluster_mode=input.cluster_mode or "single-node",
                cluster_size=input.cluster_size or 1,
                startup_command=input.startup_command,
                bootstrap_script=input.bootstrap_script,
                environ=environ,
                preset_values=preset_values,
            )
        )
        result = await self._processors.deployment_revision_preset.create.wait_for_complete(
            CreateDeploymentRevisionPresetAction(creator=creator)
        )
        return CreateDeploymentRevisionPresetPayload(preset=self._data_to_node(result.preset))

    async def update(
        self,
        input: UpdateDeploymentRevisionPresetInput,
    ) -> UpdateDeploymentRevisionPresetPayload:
        resource_slots_state: OptionalState[list[ResourceSlotEntry]] = (
            OptionalState.update(self._convert_resource_slots_input(input.resource_slots))
            if input.resource_slots is not None
            else OptionalState.nop()
        )
        environ_state: OptionalState[dict[str, str]] = (
            OptionalState.update(self._convert_environ_input(input.environ))
            if input.environ is not None
            else OptionalState.nop()
        )
        preset_values_state: OptionalState[list[PresetValueEntry]] = (
            OptionalState.update(self._convert_preset_values_input(input.preset_values))
            if input.preset_values is not None
            else OptionalState.nop()
        )
        model_def_state: TriState[ModelDefinition] = self._convert_model_definition_state(
            input.model_definition
        )

        spec = DeploymentRevisionPresetUpdaterSpec(
            name=(
                OptionalState.update(input.name) if input.name is not None else OptionalState.nop()
            ),
            description=(
                TriState.nop()
                if input.description is SENTINEL
                else TriState.nullify()
                if input.description is None
                else TriState.update(input.description)
            ),
            rank=(
                OptionalState.update(input.rank) if input.rank is not None else OptionalState.nop()
            ),
            image=(
                TriState.nop()
                if input.image is SENTINEL
                else TriState.nullify()
                if input.image is None
                else TriState.update(input.image)
            ),
            model_definition=model_def_state,
            resource_slots=resource_slots_state,
            resource_opts=(
                OptionalState.update(self._convert_resource_opts_input(input.resource_opts))
                if input.resource_opts is not None
                else OptionalState.nop()
            ),
            cluster_mode=(
                OptionalState.update(input.cluster_mode)
                if input.cluster_mode is not None
                else OptionalState.nop()
            ),
            cluster_size=(
                OptionalState.update(input.cluster_size)
                if input.cluster_size is not None
                else OptionalState.nop()
            ),
            startup_command=(
                TriState.nop()
                if input.startup_command is SENTINEL
                else TriState.nullify()
                if input.startup_command is None
                else TriState.update(input.startup_command)
            ),
            bootstrap_script=(
                TriState.nop()
                if input.bootstrap_script is SENTINEL
                else TriState.nullify()
                if input.bootstrap_script is None
                else TriState.update(input.bootstrap_script)
            ),
            environ=environ_state,
            preset_values=preset_values_state,
        )
        updater: Updater[DeploymentRevisionPresetRow] = Updater(spec=spec, pk_value=input.id)
        result = await self._processors.deployment_revision_preset.update.wait_for_complete(
            UpdateDeploymentRevisionPresetAction(id=input.id, updater=updater)
        )
        return UpdateDeploymentRevisionPresetPayload(preset=self._data_to_node(result.preset))

    async def delete(self, preset_id: UUID) -> DeleteDeploymentRevisionPresetPayload:
        result = await self._processors.deployment_revision_preset.delete.wait_for_complete(
            DeleteDeploymentRevisionPresetAction(id=preset_id)
        )
        return DeleteDeploymentRevisionPresetPayload(id=result.preset.id)

    def _convert_filter(self, filter_: DeploymentRevisionPresetFilter) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
        if filter_.runtime_variant_id is not None:
            conditions.append(
                DeploymentRevisionPresetConditions.by_runtime_variant_id(filter_.runtime_variant_id)
            )
        if filter_.name:
            cond = self.convert_string_filter(
                filter_.name,
                contains_factory=DeploymentRevisionPresetConditions.by_name_contains,
                equals_factory=DeploymentRevisionPresetConditions.by_name_equals,
                starts_with_factory=DeploymentRevisionPresetConditions.by_name_starts_with,
                ends_with_factory=DeploymentRevisionPresetConditions.by_name_ends_with,
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

    def _convert_orders(self, orders: list[DeploymentRevisionPresetOrder]) -> list[QueryOrder]:
        result: list[QueryOrder] = []
        for order in orders:
            ascending = order.direction.value == "ASC"
            match order.field:
                case DeploymentRevisionPresetOrderField.NAME:
                    result.append(DeploymentRevisionPresetOrders.name(ascending))
                case DeploymentRevisionPresetOrderField.RANK:
                    result.append(DeploymentRevisionPresetOrders.rank(ascending))
                case DeploymentRevisionPresetOrderField.CREATED_AT:
                    result.append(DeploymentRevisionPresetOrders.created_at(ascending))
        return result

    @staticmethod
    def _convert_resource_slots_input(
        slots: list[Any] | None,
    ) -> list[ResourceSlotEntry]:
        if not slots:
            return []
        return [
            ResourceSlotEntry(resource_type=s.resource_type, quantity=s.quantity) for s in slots
        ]

    @staticmethod
    def _convert_environ_input(
        environ: list[Any] | None,
    ) -> dict[str, str]:
        if not environ:
            return {}
        return {e.key: e.value for e in environ}

    @staticmethod
    def _convert_resource_opts_input(
        resource_opts: list[Any] | None,
    ) -> list[ResourceOptsEntry]:
        if not resource_opts:
            return []
        return [ResourceOptsEntry(name=o.name, value=o.value) for o in resource_opts]

    @staticmethod
    def _convert_preset_values_input(
        preset_values: list[Any] | None,
    ) -> list[PresetValueEntry]:
        if not preset_values:
            return []
        return [PresetValueEntry(preset_id=pv.preset_id, value=pv.value) for pv in preset_values]

    @staticmethod
    def _convert_model_definition_state(
        value: Any,
    ) -> TriState[ModelDefinition]:
        if value is SENTINEL:
            return TriState.nop()
        if value is None:
            return TriState.nullify()
        return TriState.update(ModelDefinition(**value))

    @staticmethod
    def _data_to_node(
        data: DeploymentRevisionPresetData,
    ) -> DeploymentRevisionPresetNode:
        environ_entries = [EnvironEntryInfo(key=e.key, value=e.value) for e in (data.environ or [])]
        resource_slot_entries = [
            ResourceSlotEntryInfo(resource_type=s.resource_type, quantity=s.quantity)
            for s in (data.resource_slots or [])
        ]
        resource_opts_entries = [
            ResourceOptsEntryInfo(name=o.name, value=o.value) for o in (data.resource_opts or [])
        ]
        preset_value_entries = [
            PresetValueInfo(preset_id=pv.preset_id, value=pv.value)
            for pv in (data.preset_values or [])
        ]
        return DeploymentRevisionPresetNode(
            id=data.id,
            runtime_variant_id=data.runtime_variant_id,
            name=data.name,
            description=data.description,
            rank=data.rank,
            cluster=PresetClusterSpec(
                cluster_mode=data.cluster_mode,
                cluster_size=data.cluster_size,
            ),
            resource=PresetResourceAllocation(
                resource_slots=resource_slot_entries,
                resource_opts=resource_opts_entries,
            ),
            execution=PresetExecutionSpec(
                image=data.image,
                startup_command=data.startup_command,
                bootstrap_script=data.bootstrap_script,
                environ=environ_entries,
            ),
            model_definition=data.model_definition,
            preset_values=preset_value_entries,
            created_at=data.created_at,
            updated_at=data.updated_at,
        )
