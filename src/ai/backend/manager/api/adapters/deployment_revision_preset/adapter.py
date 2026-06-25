from __future__ import annotations

from typing import Any
from uuid import UUID

from ai.backend.common.api_handlers import SENTINEL, Sentinel
from ai.backend.common.config import (
    ModelConfig,
    ModelDefinition,
    ModelHealthCheck,
    ModelMetadata,
    ModelServiceConfig,
    PreStartAction,
)
from ai.backend.common.data.model_deployment.types import DeploymentStrategy
from ai.backend.common.dto.manager.v2.deployment.request import DeploymentStrategyInput
from ai.backend.common.dto.manager.v2.deployment.types import (
    ModelConfigInfoDTO,
    ModelDefinitionInfoDTO,
    ModelHealthCheckInfoDTO,
    ModelMetadataInfoDTO,
    ModelServiceConfigInfoDTO,
    PreStartActionInfoDTO,
)
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
    PresetDeploymentDefaults,
    PresetExecutionSpec,
    PresetResourceAllocation,
    PresetValueInfo,
    ResourceOptsEntryInfo,
    SearchDeploymentRevisionPresetsPayload,
    UpdateDeploymentRevisionPresetPayload,
)
from ai.backend.common.dto.manager.v2.deployment_revision_preset.types import (
    DeploymentRevisionPresetOrderField,
)
from ai.backend.common.dto.manager.v2.resource_slot.request import (
    AllocatedResourceSlotFilter,
    SearchAllocatedResourceSlotsInput,
)
from ai.backend.common.dto.manager.v2.resource_slot.response import (
    AllocatedResourceSlotNode,
    SearchAllocatedResourceSlotsPayload,
)
from ai.backend.manager.api.adapter_options.pagination.pagination import PaginationSpec
from ai.backend.manager.api.adapters.base import BaseAdapter
from ai.backend.manager.data.deployment_revision_preset.types import (
    DeploymentRevisionPresetData,
    ResourceSlotEntryData,
)
from ai.backend.manager.errors.resource import DeploymentRevisionPresetNotFound
from ai.backend.manager.models.base import ResourceOptsEntry
from ai.backend.manager.models.deployment_revision_preset.conditions import (
    DeploymentRevisionPresetConditions,
)
from ai.backend.manager.models.deployment_revision_preset.orders import (
    DeploymentRevisionPresetOrders,
)
from ai.backend.manager.models.deployment_revision_preset.row import DeploymentRevisionPresetRow
from ai.backend.manager.models.resource_slot.conditions import PresetResourceSlotConditions
from ai.backend.manager.models.resource_slot.orders import (
    ALLOCATED_SLOT_DEFAULT_BACKWARD_ORDER,
    ALLOCATED_SLOT_DEFAULT_FORWARD_ORDER,
    ALLOCATED_SLOT_PRESET_TIEBREAKER,
    resolve_allocated_slot_preset_order,
)
from ai.backend.manager.models.runtime_variant_preset.types import (
    RuntimeVariantPresetValueEntry,
)
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    QueryCondition,
    QueryOrder,
    combine_conditions_or,
)
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.deployment_revision_preset.creators import (
    DeploymentRevisionPresetCreatorSpec,
    PresetResourceSlotDependentCreatorSpec,
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
from ai.backend.manager.services.deployment_revision_preset.actions.search_resource_slots import (
    SearchPresetResourceSlotsAction,
)
from ai.backend.manager.services.deployment_revision_preset.actions.update import (
    UpdateDeploymentRevisionPresetAction,
)
from ai.backend.manager.types import OptionalState, TriState


def _preset_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=DeploymentRevisionPresetOrders.rank(ascending=True),
        backward_order=DeploymentRevisionPresetOrders.rank(ascending=False),
        forward_condition_factory=DeploymentRevisionPresetConditions.by_cursor_forward,
        backward_condition_factory=DeploymentRevisionPresetConditions.by_cursor_backward,
        tiebreaker_order=DeploymentRevisionPresetRow.id.asc(),
    )


def _preset_resource_slot_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=ALLOCATED_SLOT_DEFAULT_FORWARD_ORDER,
        backward_order=ALLOCATED_SLOT_DEFAULT_BACKWARD_ORDER,
        forward_condition_factory=PresetResourceSlotConditions.by_cursor_forward,
        backward_condition_factory=PresetResourceSlotConditions.by_cursor_backward,
        tiebreaker_order=ALLOCATED_SLOT_PRESET_TIEBREAKER,
    )


def _pre_start_action_to_dto(action: PreStartAction) -> PreStartActionInfoDTO:
    return PreStartActionInfoDTO(action=action.action, args=action.args)


def _model_health_check_to_dto(check: ModelHealthCheck) -> ModelHealthCheckInfoDTO:
    return ModelHealthCheckInfoDTO(
        enable=check.enable,
        interval=check.interval,
        path=check.path,
        max_retries=check.max_retries,
        max_wait_time=check.max_wait_time,
        expected_status_code=check.expected_status_code,
        initial_delay=check.initial_delay,
    )


def _model_service_config_to_dto(service: ModelServiceConfig) -> ModelServiceConfigInfoDTO:
    return ModelServiceConfigInfoDTO(
        pre_start_actions=[_pre_start_action_to_dto(a) for a in service.pre_start_actions],
        start_command=service.start_command,
        shell=service.shell,
        port=service.port,
        health_check=(
            _model_health_check_to_dto(service.health_check)
            if service.health_check is not None
            else None
        ),
    )


def _model_metadata_to_dto(metadata: ModelMetadata) -> ModelMetadataInfoDTO:
    return ModelMetadataInfoDTO(
        author=metadata.author,
        title=metadata.title,
        version=metadata.version,
        created=metadata.created,
        last_modified=metadata.last_modified,
        description=metadata.description,
        task=metadata.task,
        category=metadata.category,
        architecture=metadata.architecture,
        framework=metadata.framework,
        label=metadata.label,
        license=metadata.license,
        min_resource=metadata.min_resource,
    )


def _model_config_to_dto(config: ModelConfig) -> ModelConfigInfoDTO:
    return ModelConfigInfoDTO(
        name=config.name,
        model_path=config.model_path,
        service=(
            _model_service_config_to_dto(config.service) if config.service is not None else None
        ),
        metadata=(_model_metadata_to_dto(config.metadata) if config.metadata is not None else None),
    )


def _model_definition_to_dto(
    definition: ModelDefinition | None,
) -> ModelDefinitionInfoDTO | None:
    if definition is None:
        return None
    return ModelDefinitionInfoDTO(
        models=[_model_config_to_dto(m) for m in definition.models],
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
        slot_specs = [
            PresetResourceSlotDependentCreatorSpec(entry=entry) for entry in resource_slots
        ]
        resource_opts = self._convert_resource_opts_input(input.resource_opts)
        environ = self._convert_environ_input(input.environ)
        preset_values = self._convert_preset_values_input(input.preset_values)
        # FIXME: temporary bridge — fold the single-string `command` into the
        # str `start_command` so the ModelServiceConfig validator wraps it.
        model_def: ModelDefinition | None = None
        if input.model_definition is not None:
            model_definition_payload = input.model_definition.model_dump()
            for model_payload in model_definition_payload["models"]:
                service_payload = model_payload["service"]
                command = service_payload.pop("command", None)
                if command is not None:
                    service_payload["start_command"] = command
            # ModelServiceConfig will convert the `start_command` string into a list of strings for the `start_command` field.
            model_def = ModelDefinition.model_validate(model_definition_payload)
        strategy, strategy_spec = self._convert_required_strategy_input(input.deployment_strategy)

        spec = DeploymentRevisionPresetCreatorSpec(
            runtime_variant_id=input.runtime_variant_id,
            name=input.name,
            description=input.description,
            image_id=input.image_id,
            model_definition=model_def,
            resource_opts=resource_opts,
            cluster_mode=input.cluster_mode,
            cluster_size=input.cluster_size,
            startup_command=input.startup_command,
            bootstrap_script=input.bootstrap_script,
            environ=environ,
            runtime_variant_preset_values=preset_values,
            open_to_public=input.open_to_public,
            replica_count=input.replica_count,
            revision_history_limit=input.revision_history_limit,
            deployment_strategy=strategy,
            deployment_strategy_spec=strategy_spec,
        )
        result = await self._processors.deployment_revision_preset.create.wait_for_complete(
            CreateDeploymentRevisionPresetAction(creator_spec=spec, resource_slot_specs=slot_specs)
        )
        return CreateDeploymentRevisionPresetPayload(preset=self._data_to_node(result.preset))

    async def update(
        self,
        input: UpdateDeploymentRevisionPresetInput,
    ) -> UpdateDeploymentRevisionPresetPayload:
        slot_specs: list[PresetResourceSlotDependentCreatorSpec] | None = (
            [
                PresetResourceSlotDependentCreatorSpec(entry=entry)
                for entry in self._convert_resource_slots_input(input.resource_slots)
            ]
            if input.resource_slots is not None
            else None
        )
        environ_state: OptionalState[dict[str, str]] = (
            OptionalState.update(self._convert_environ_input(input.environ))
            if input.environ is not None
            else OptionalState.nop()
        )
        preset_values_state: OptionalState[list[RuntimeVariantPresetValueEntry]] = (
            OptionalState.update(self._convert_preset_values_input(input.preset_values))
            if input.preset_values is not None
            else OptionalState.nop()
        )
        model_def_state: TriState[ModelDefinition] = self._convert_model_definition_state(
            input.model_definition
        )

        spec = DeploymentRevisionPresetUpdaterSpec(
            runtime_variant=(
                OptionalState.update(input.runtime_variant_id)
                if input.runtime_variant_id is not None
                else OptionalState.nop()
            ),
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
            image_id=(
                TriState.nop()
                if input.image_id is SENTINEL
                else TriState.nullify()
                if input.image_id is None
                else TriState.update(input.image_id)
            ),
            model_definition=model_def_state,
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
            runtime_variant_preset_values=preset_values_state,
            open_to_public=self._convert_tri_state(input.open_to_public),
            replica_count=self._convert_tri_state(input.replica_count),
            revision_history_limit=self._convert_tri_state(input.revision_history_limit),
            deployment_strategy=self._convert_strategy_update_state(input.deployment_strategy),
            deployment_strategy_spec=self._convert_strategy_spec_update_state(
                input.deployment_strategy
            ),
        )
        updater: Updater[DeploymentRevisionPresetRow] = Updater(spec=spec, pk_value=input.id)
        result = await self._processors.deployment_revision_preset.update.wait_for_complete(
            UpdateDeploymentRevisionPresetAction(
                id=input.id, updater=updater, resource_slot_specs=slot_specs
            )
        )
        return UpdateDeploymentRevisionPresetPayload(preset=self._data_to_node(result.preset))

    async def delete(self, preset_id: UUID) -> DeleteDeploymentRevisionPresetPayload:
        result = await self._processors.deployment_revision_preset.delete.wait_for_complete(
            DeleteDeploymentRevisionPresetAction(id=preset_id)
        )
        return DeleteDeploymentRevisionPresetPayload(id=result.preset.id)

    async def search_resource_slots(
        self,
        preset_id: UUID,
        input: SearchAllocatedResourceSlotsInput,
    ) -> SearchAllocatedResourceSlotsPayload:
        """Search resource slots allocated to a deployment revision preset."""
        querier = self._build_preset_resource_slot_querier(input, preset_id=preset_id)
        action_result = await self._processors.deployment_revision_preset.search_resource_slots.wait_for_complete(
            SearchPresetResourceSlotsAction(
                preset_id=preset_id,
                querier=querier,
            )
        )
        return SearchAllocatedResourceSlotsPayload(
            items=[
                AllocatedResourceSlotNode(slot_name=slot_name, quantity=quantity)
                for slot_name, quantity in action_result.items
            ],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    def _build_preset_resource_slot_querier(
        self,
        input: SearchAllocatedResourceSlotsInput,
        preset_id: UUID,
    ) -> BatchQuerier:
        conditions: list[QueryCondition] = [
            PresetResourceSlotConditions.by_preset_id(preset_id),
        ]
        if input.filter:
            conditions.extend(self._convert_allocated_slot_filter(input.filter))
        orders: list[QueryOrder] = (
            [resolve_allocated_slot_preset_order(o.field, o.direction) for o in input.order]
            if input.order
            else []
        )
        return self._build_querier(
            conditions=conditions,
            orders=orders,
            pagination_spec=_preset_resource_slot_pagination_spec(),
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )

    def _convert_allocated_slot_filter(
        self,
        filter_: AllocatedResourceSlotFilter,
    ) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
        if filter_.slot_name is not None:
            cond = self.convert_string_filter(
                filter_.slot_name,
                contains_factory=PresetResourceSlotConditions.by_slot_name_contains,
                equals_factory=PresetResourceSlotConditions.by_slot_name_equals,
                starts_with_factory=PresetResourceSlotConditions.by_slot_name_starts_with,
                ends_with_factory=PresetResourceSlotConditions.by_slot_name_ends_with,
                in_factory=PresetResourceSlotConditions.by_slot_name_in,
            )
            if cond is not None:
                conditions.append(cond)
        if filter_.AND:
            for sub in filter_.AND:
                conditions.extend(self._convert_allocated_slot_filter(sub))
        if filter_.OR:
            or_conds: list[QueryCondition] = []
            for sub in filter_.OR:
                or_conds.extend(self._convert_allocated_slot_filter(sub))
            if or_conds:
                conditions.append(combine_conditions_or(or_conds))
        return conditions

    def _convert_filter(self, filter_: DeploymentRevisionPresetFilter) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
        if filter_.id is not None:
            cond = self.convert_uuid_filter(
                filter_.id,
                equals_factory=DeploymentRevisionPresetConditions.by_id_equals,
                in_factory=DeploymentRevisionPresetConditions.by_id_in,
            )
            if cond is not None:
                conditions.append(cond)
        if filter_.runtime_variant_id is not None:
            cond = self.convert_uuid_filter(
                filter_.runtime_variant_id,
                equals_factory=DeploymentRevisionPresetConditions.by_runtime_variant_id_equals,
                in_factory=DeploymentRevisionPresetConditions.by_runtime_variant_id_in,
            )
            if cond is not None:
                conditions.append(cond)
        if filter_.name:
            cond = self.convert_string_filter(
                filter_.name,
                contains_factory=DeploymentRevisionPresetConditions.by_name_contains,
                equals_factory=DeploymentRevisionPresetConditions.by_name_equals,
                starts_with_factory=DeploymentRevisionPresetConditions.by_name_starts_with,
                ends_with_factory=DeploymentRevisionPresetConditions.by_name_ends_with,
                in_factory=DeploymentRevisionPresetConditions.by_name_in,
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
    ) -> list[ResourceSlotEntryData]:
        if not slots:
            return []
        return [
            ResourceSlotEntryData(resource_type=s.resource_type, quantity=s.quantity) for s in slots
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
    ) -> list[RuntimeVariantPresetValueEntry]:
        if not preset_values:
            return []
        return [
            RuntimeVariantPresetValueEntry(preset_id=pv.preset_id, value=pv.value)
            for pv in preset_values
        ]

    @staticmethod
    def _convert_model_definition_state(
        value: ModelDefinition | Sentinel | None,
    ) -> TriState[ModelDefinition]:
        if value is SENTINEL:
            return TriState.nop()
        if value is None:
            return TriState.nullify()
        return TriState.update(value)

    @staticmethod
    def _convert_tri_state(value: Any) -> TriState[Any]:
        """Convert a Sentinel | None | T input to TriState."""
        if value is SENTINEL:
            return TriState.nop()
        if value is None:
            return TriState.nullify()
        return TriState.update(value)

    @staticmethod
    def _convert_strategy_input(
        strategy_input: DeploymentStrategyInput | None,
    ) -> tuple[DeploymentStrategy | None, dict[str, Any] | None]:
        """Convert DeploymentStrategyInput to (strategy, strategy_spec dict)."""
        if strategy_input is None:
            return None, None
        match strategy_input.type:
            case DeploymentStrategy.ROLLING:
                rolling = strategy_input.rolling_update
                spec_dict: dict[str, Any] = (
                    rolling.model_dump(mode="json") if rolling is not None else {}
                )
                return DeploymentStrategy.ROLLING, spec_dict
            case DeploymentStrategy.BLUE_GREEN:
                bg = strategy_input.blue_green
                spec_dict = bg.model_dump(mode="json") if bg is not None else {}
                return DeploymentStrategy.BLUE_GREEN, spec_dict

    def _convert_required_strategy_input(
        self,
        strategy_input: DeploymentStrategyInput,
    ) -> tuple[DeploymentStrategy, dict[str, Any]]:
        """Convert a non-null DeploymentStrategyInput to (strategy, strategy_spec dict)."""
        match strategy_input.type:
            case DeploymentStrategy.ROLLING:
                rolling = strategy_input.rolling_update
                spec_dict: dict[str, Any] = (
                    rolling.model_dump(mode="json") if rolling is not None else {}
                )
                return DeploymentStrategy.ROLLING, spec_dict
            case DeploymentStrategy.BLUE_GREEN:
                bg = strategy_input.blue_green
                spec_dict = bg.model_dump(mode="json") if bg is not None else {}
                return DeploymentStrategy.BLUE_GREEN, spec_dict

    @classmethod
    def _convert_strategy_update_state(
        cls,
        strategy_input: Any,
    ) -> TriState[DeploymentStrategy]:
        if strategy_input is SENTINEL:
            return TriState.nop()
        if strategy_input is None:
            return TriState.nullify()
        strategy, _ = cls._convert_strategy_input(strategy_input)
        if strategy is None:
            return TriState.nullify()
        return TriState.update(strategy)

    @classmethod
    def _convert_strategy_spec_update_state(
        cls,
        strategy_input: Any,
    ) -> TriState[dict[str, Any]]:
        if strategy_input is SENTINEL:
            return TriState.nop()
        if strategy_input is None:
            return TriState.nullify()
        _, spec = cls._convert_strategy_input(strategy_input)
        if spec is None:
            return TriState.nullify()
        return TriState.update(spec)

    @staticmethod
    def _data_to_node(
        data: DeploymentRevisionPresetData,
    ) -> DeploymentRevisionPresetNode:
        environ_entries = [EnvironEntryInfo(key=e.key, value=e.value) for e in (data.environ or [])]
        resource_opts_entries = [
            ResourceOptsEntryInfo(name=o.name, value=o.value) for o in (data.resource_opts or [])
        ]
        preset_value_entries = [
            PresetValueInfo(preset_id=pv.preset_id, value=pv.value)
            for pv in (data.runtime_variant_preset_values or [])
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
                resource_opts=resource_opts_entries,
            ),
            execution=PresetExecutionSpec(
                image_id=data.image_id,
                startup_command=data.startup_command,
                bootstrap_script=data.bootstrap_script,
                environ=environ_entries,
            ),
            deployment_defaults=PresetDeploymentDefaults(
                open_to_public=data.open_to_public,
                replica_count=data.replica_count,
                revision_history_limit=data.revision_history_limit,
                deployment_strategy=data.deployment_strategy,
                deployment_strategy_spec=data.deployment_strategy_spec,
            ),
            model_definition=_model_definition_to_dto(data.model_definition),
            preset_values=preset_value_entries,
            created_at=data.created_at,
            updated_at=data.updated_at,
        )
