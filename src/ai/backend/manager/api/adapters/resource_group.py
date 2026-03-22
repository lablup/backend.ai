"""Resource group adapter bridging DTOs and Processors."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from ai.backend.common.api_handlers import SENTINEL
from ai.backend.common.data.filter_specs import StringMatchSpec
from ai.backend.common.dto.manager.v2.fair_share.types import (
    ResourceSlotEntryInfo,
    ResourceSlotInfo,
    ResourceWeightEntryInfo,
)
from ai.backend.common.dto.manager.v2.resource_group.request import (
    AdminSearchResourceGroupsInput,
    CreateResourceGroupInput,
    ResourceGroupFilter,
    ResourceGroupOrder,
    UpdateResourceGroupConfigInput,
    UpdateResourceGroupFairShareSpecInput,
    UpdateResourceGroupInput,
)
from ai.backend.common.dto.manager.v2.resource_group.response import (
    CreateResourceGroupPayload,
    FairShareScalingGroupSpecInfo,
    PreemptionConfigInfo,
    ResourceGroupDetailNode,
    ResourceGroupMetadataInfo,
    ResourceGroupNetworkConfigInfo,
    ResourceGroupNode,
    ResourceGroupSchedulerConfigInfo,
    ResourceGroupStatusInfo,
    ResourceInfoNode,
    UpdateResourceGroupConfigPayloadNode,
    UpdateResourceGroupFairShareSpecPayloadNode,
    UpdateResourceGroupPayload,
)
from ai.backend.common.dto.manager.v2.resource_group.types import (
    PreemptionModeDTO,
    PreemptionOrderDTO,
    ResourceGroupOrderDirection,
    ResourceGroupOrderField,
    SchedulerTypeDTO,
)
from ai.backend.common.types import PreemptionMode, PreemptionOrder, SlotQuantity
from ai.backend.manager.data.scaling_group.types import (
    PreemptionConfig as DataPreemptionConfig,
)
from ai.backend.manager.data.scaling_group.types import (
    ScalingGroupData,
    SchedulerType,
)
from ai.backend.manager.errors.resource import ScalingGroupNotFound
from ai.backend.manager.models.scaling_group import ScalingGroupRow
from ai.backend.manager.models.scaling_group.conditions import ScalingGroupConditions
from ai.backend.manager.models.scaling_group.orders import ScalingGroupOrders
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    NoPagination,
    OffsetPagination,
    QueryCondition,
    combine_conditions_or,
    negate_conditions,
)
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.base.purger import Purger
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.scaling_group.creators import ScalingGroupCreatorSpec
from ai.backend.manager.repositories.scaling_group.updaters import (
    ScalingGroupMetadataUpdaterSpec,
    ScalingGroupNetworkConfigUpdaterSpec,
    ScalingGroupSchedulerConfigUpdaterSpec,
    ScalingGroupStatusUpdaterSpec,
    ScalingGroupUpdaterSpec,
)
from ai.backend.manager.services.scaling_group.actions.create import CreateScalingGroupAction
from ai.backend.manager.services.scaling_group.actions.get_resource_info import (
    GetResourceInfoAction,
)
from ai.backend.manager.services.scaling_group.actions.list_scaling_groups import (
    SearchScalingGroupsAction,
)
from ai.backend.manager.services.scaling_group.actions.modify import ModifyScalingGroupAction
from ai.backend.manager.services.scaling_group.actions.purge_scaling_group import (
    PurgeScalingGroupAction,
)
from ai.backend.manager.services.scaling_group.actions.update_fair_share_spec import (
    ResourceWeightInput,
    UpdateFairShareSpecAction,
)
from ai.backend.manager.types import OptionalState, TriState

from .base import BaseAdapter
from .pagination import PaginationSpec


def _normalize_quantity(value: Decimal) -> Decimal:
    """Normalize a Decimal by removing trailing zeros without scientific notation.

    PostgreSQL NUMERIC(24, 6) preserves scale=6 through SUM() aggregation,
    producing values like Decimal('7.000000'). This function strips trailing
    zeros while avoiding scientific notation for large integer values.

    Examples:
        Decimal('7.000000') -> Decimal('7')
        Decimal('0.500000') -> Decimal('0.5')
        Decimal('4294967296.000000') -> Decimal('4294967296')
    """
    normalized = value.normalize()
    sign, digits, exponent = normalized.as_tuple()
    if isinstance(exponent, int) and exponent > 0:
        # normalize() may produce scientific notation for large integers
        # (e.g., Decimal('1000000000') -> Decimal('1E+9')).
        # Convert back to plain integer representation.
        return Decimal(int(normalized))
    return normalized


def _slot_quantities_to_resource_slot_info(
    quantities: list[SlotQuantity],
) -> ResourceSlotInfo:
    """Convert a list of SlotQuantity to a ResourceSlotInfo DTO with normalized quantities."""
    return ResourceSlotInfo(
        entries=[
            ResourceSlotEntryInfo(
                resource_type=sq.slot_name,
                quantity=_normalize_quantity(sq.quantity),
            )
            for sq in quantities
        ]
    )


def _resource_group_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=ScalingGroupOrders.created_at(ascending=False),
        backward_order=ScalingGroupOrders.created_at(ascending=True),
        forward_condition_factory=ScalingGroupConditions.by_cursor_forward,
        backward_condition_factory=ScalingGroupConditions.by_cursor_backward,
        tiebreaker_order=ScalingGroupRow.name.asc(),
    )


@dataclass
class ResourceGroupSearchPayload:
    """Result of a resource group search containing paginated ResourceGroupDetailNode items."""

    items: list[ResourceGroupDetailNode]
    total_count: int
    has_next_page: bool
    has_previous_page: bool


# Sentinel UUID used when converting ScalingGroupData to ResourceGroupNode.
# ScalingGroupData does not have a UUID field (name is the primary key),
# so this zero-UUID signals that the id field is not populated from actual data.
_EMPTY_UUID = UUID(int=0)


class ResourceGroupAdapter(BaseAdapter):
    """Adapter for resource group (scaling group) operations.

    Bridges CreateResourceGroupInput / UpdateResourceGroupInput DTOs to
    ScalingGroup Processor actions and converts results back to Pydantic DTOs.

    Note on ResourceGroupNode.id:
        ScalingGroupData uses ``name`` (str) as primary key.  ResourceGroupNode
        declares ``id: UUID`` for DTO consistency with other domains.  When
        converting from ScalingGroupData the ``id`` field is set to a sentinel
        zero-UUID because no UUID is available in the data model.  Callers that
        need an opaque identifier should use the ``name`` field instead.
    """

    async def batch_load_by_names(
        self, names: Sequence[str]
    ) -> list[ResourceGroupDetailNode | None]:
        """Batch load resource groups by name for DataLoader use.

        Returns ResourceGroupDetailNode items in the same order as the input names list.
        """
        if not names:
            return []
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=len(names)),
            conditions=[ScalingGroupConditions.by_names(names)],
        )
        action_result = (
            await self._processors.scaling_group.search_scaling_groups.wait_for_complete(
                SearchScalingGroupsAction(querier=querier)
            )
        )
        rg_map = {sg.name: sg for sg in action_result.scaling_groups}
        return [
            self._data_to_detail_node(rg_map[name]) if name in rg_map else None for name in names
        ]

    async def search(self, input: AdminSearchResourceGroupsInput) -> ResourceGroupSearchPayload:
        """Search resource groups with filters, ordering, and pagination."""
        conditions = self._convert_filter(input.filter) if input.filter else []
        orders = self._convert_orders(input.order) if input.order else []
        pagination_spec = _resource_group_pagination_spec()
        querier = self._build_querier(
            conditions=conditions,
            orders=orders,
            pagination_spec=pagination_spec,
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )
        action_result = (
            await self._processors.scaling_group.search_scaling_groups.wait_for_complete(
                SearchScalingGroupsAction(querier=querier)
            )
        )
        return ResourceGroupSearchPayload(
            items=[self._data_to_detail_node(sg) for sg in action_result.scaling_groups],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    def _convert_filter(self, filter_: ResourceGroupFilter) -> list[QueryCondition]:
        """Convert ResourceGroupFilter DTO to QueryConditions."""
        conditions: list[QueryCondition] = []
        if filter_.name:
            cond = self.convert_string_filter(
                filter_.name,
                contains_factory=ScalingGroupConditions.by_name_contains,
                equals_factory=ScalingGroupConditions.by_name_equals,
                starts_with_factory=ScalingGroupConditions.by_name_starts_with,
                ends_with_factory=ScalingGroupConditions.by_name_ends_with,
            )
            if cond:
                conditions.append(cond)
        if filter_.description:
            cond = self.convert_string_filter(
                filter_.description,
                contains_factory=ScalingGroupConditions.by_description_contains,
                equals_factory=ScalingGroupConditions.by_description_equals,
                starts_with_factory=ScalingGroupConditions.by_description_starts_with,
                ends_with_factory=ScalingGroupConditions.by_description_ends_with,
            )
            if cond:
                conditions.append(cond)
        if filter_.is_active is not None:
            conditions.append(ScalingGroupConditions.by_is_active(filter_.is_active))
        if filter_.is_public is not None:
            conditions.append(ScalingGroupConditions.by_is_public(filter_.is_public))
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

    def _convert_orders(self, orders: list[ResourceGroupOrder]) -> list[Any]:
        """Convert ResourceGroupOrder DTOs to QueryOrders."""
        result = []
        for order in orders:
            ascending = order.direction == ResourceGroupOrderDirection.ASC
            match order.field:
                case ResourceGroupOrderField.NAME:
                    result.append(ScalingGroupOrders.name(ascending))
                case ResourceGroupOrderField.CREATED_AT:
                    result.append(ScalingGroupOrders.created_at(ascending))
                case ResourceGroupOrderField.IS_ACTIVE:
                    result.append(ScalingGroupOrders.is_active(ascending))
        return result

    async def create(
        self,
        input: CreateResourceGroupInput,
    ) -> CreateResourceGroupPayload:
        """Create a new resource group.

        Args:
            input: Pydantic DTO with creation parameters.

        Returns:
            Pydantic payload containing the created resource group node.
        """
        creator_spec = ScalingGroupCreatorSpec(
            name=input.name,
            # ScalingGroupCreatorSpec requires driver and scheduler fields
            # which are not exposed in CreateResourceGroupInput.
            # Default to "static" driver and "fifo" scheduler as reasonable defaults.
            driver="static",
            scheduler="fifo",
            description=input.description,
            is_active=True,
        )
        creator = Creator(spec=creator_spec)
        action_result = await self._processors.scaling_group.create_scaling_group.wait_for_complete(
            CreateScalingGroupAction(creator=creator)
        )

        return CreateResourceGroupPayload(
            resource_group=self._data_to_node(action_result.scaling_group),
        )

    async def update(
        self,
        name: str,
        input: UpdateResourceGroupInput,
    ) -> UpdateResourceGroupPayload:
        """Update an existing resource group.

        Args:
            name: Name of the resource group to update.
            input: Pydantic DTO with partial update parameters.

        Returns:
            Pydantic payload containing the updated resource group node.
        """
        status_spec = ScalingGroupStatusUpdaterSpec(
            is_active=(
                OptionalState.update(input.is_active)
                if input.is_active is not None
                else OptionalState.nop()
            ),
        )
        metadata_spec = ScalingGroupMetadataUpdaterSpec(
            description=(
                TriState.nullify()
                if input.description is SENTINEL
                else (
                    TriState.update(str(input.description))
                    if input.description is not None
                    else TriState.nop()
                )
            ),
        )
        updater_spec = ScalingGroupUpdaterSpec(
            status=status_spec,
            metadata=metadata_spec,
        )
        updater = Updater(spec=updater_spec, pk_value=name)
        action_result = await self._processors.scaling_group.modify_scaling_group.wait_for_complete(
            ModifyScalingGroupAction(updater=updater)
        )

        return UpdateResourceGroupPayload(
            resource_group=self._data_to_node(action_result.scaling_group),
        )

    async def get_resource_info(self, scaling_group: str) -> ResourceInfoNode:
        """Get resource information for a scaling group.

        Args:
            scaling_group: Name of the scaling group.

        Returns:
            ResourceInfoNode DTO with capacity, used, and free resource metrics.
            Quantities are normalized (trailing zeros removed, no scientific notation).
        """
        action_result = await self._processors.scaling_group.get_resource_info.wait_for_complete(
            GetResourceInfoAction(scaling_group=scaling_group)
        )
        raw = action_result.resource_info
        return ResourceInfoNode(
            capacity=_slot_quantities_to_resource_slot_info(raw.capacity),
            used=_slot_quantities_to_resource_slot_info(raw.used),
            free=_slot_quantities_to_resource_slot_info(raw.free),
        )

    async def get_fair_share_spec(
        self,
        resource_group: str,
    ) -> FairShareScalingGroupSpecInfo:
        """Get fair share spec merged with capacity resource weights for a resource group.

        Merges the resource group's fair share spec with the current capacity
        so that resource_weights contains entries for all available resource types.
        Missing resource types use default_weight.

        Returns:
            FairShareScalingGroupSpecInfo DTO with merged resource weights and
            uses_default indicators per resource type.
        """
        name_spec = StringMatchSpec(
            value=resource_group,
            case_insensitive=False,
            negated=False,
        )
        querier = BatchQuerier(
            pagination=NoPagination(),
            conditions=[ScalingGroupConditions.by_name_equals(name_spec)],
        )
        search_result = (
            await self._processors.scaling_group.search_scaling_groups.wait_for_complete(
                SearchScalingGroupsAction(querier=querier)
            )
        )
        if not search_result.scaling_groups:
            raise ScalingGroupNotFound(resource_group)
        sg_data = search_result.scaling_groups[0]

        resource_info = await self.get_resource_info(resource_group)
        capacity = resource_info.capacity

        spec = sg_data.fair_share_spec
        weight_entries: list[ResourceWeightEntryInfo] = []

        for entry in capacity.entries:
            resource_type = entry.resource_type
            if resource_type in spec.resource_weights.data:
                weight = spec.resource_weights.data[resource_type]
                uses_default = False
            else:
                weight = spec.default_weight
                uses_default = True
            weight_entries.append(
                ResourceWeightEntryInfo(
                    resource_type=resource_type,
                    weight=weight,
                    uses_default=uses_default,
                )
            )

        return FairShareScalingGroupSpecInfo(
            half_life_days=spec.half_life_days,
            lookback_days=spec.lookback_days,
            decay_unit_days=spec.decay_unit_days,
            default_weight=spec.default_weight,
            resource_weights=weight_entries,
        )

    async def update_fair_share_spec(
        self,
        input: UpdateResourceGroupFairShareSpecInput,
    ) -> UpdateResourceGroupFairShareSpecPayloadNode:
        """Update fair share spec for a resource group.

        Args:
            input: Pydantic DTO with partial fair share spec update parameters.

        Returns:
            Payload DTO containing the updated resource group.
        """
        resource_weights = None
        if input.resource_weights is not None:
            resource_weights = [
                ResourceWeightInput(
                    resource_type=entry.resource_type,
                    weight=entry.weight,
                )
                for entry in input.resource_weights
            ]

        action_result = (
            await self._processors.scaling_group.update_fair_share_spec.wait_for_complete(
                UpdateFairShareSpecAction(
                    resource_group=input.resource_group_name,
                    half_life_days=input.half_life_days,
                    lookback_days=input.lookback_days,
                    decay_unit_days=input.decay_unit_days,
                    default_weight=input.default_weight,
                    resource_weights=resource_weights,
                )
            )
        )
        return UpdateResourceGroupFairShareSpecPayloadNode(
            resource_group=self._data_to_detail_node(action_result.scaling_group),
        )

    async def update_config(
        self,
        input: UpdateResourceGroupConfigInput,
    ) -> UpdateResourceGroupConfigPayloadNode:
        """Update resource group configuration (status, metadata, network, scheduler).

        Args:
            input: Pydantic DTO with partial configuration update parameters.

        Returns:
            Payload DTO containing the updated resource group.
        """
        status_spec = ScalingGroupStatusUpdaterSpec(
            is_active=(
                OptionalState.update(input.is_active)
                if input.is_active is not None
                else OptionalState.nop()
            ),
            is_public=(
                OptionalState.update(input.is_public)
                if input.is_public is not None
                else OptionalState.nop()
            ),
        )

        metadata_spec = ScalingGroupMetadataUpdaterSpec(
            description=(
                TriState.update(input.description)
                if input.description is not None
                else TriState.nop()
            ),
        )

        network_spec = ScalingGroupNetworkConfigUpdaterSpec(
            wsproxy_addr=(
                TriState.update(input.app_proxy_addr)
                if input.app_proxy_addr is not None
                else TriState.nop()
            ),
            wsproxy_api_token=(
                TriState.update(input.appproxy_api_token)
                if input.appproxy_api_token is not None
                else TriState.nop()
            ),
            use_host_network=(
                OptionalState.update(input.use_host_network)
                if input.use_host_network is not None
                else OptionalState.nop()
            ),
        )

        scheduler_value: str | None = None
        if input.scheduler_type is not None:
            scheduler_value = SchedulerType(input.scheduler_type).value

        preemption_config_state: OptionalState[DataPreemptionConfig] = OptionalState.nop()
        if input.preemption is not None:
            preemption_config_state = OptionalState.update(
                DataPreemptionConfig(
                    preemptible_priority=input.preemption.preemptible_priority,
                    order=PreemptionOrder(input.preemption.order),
                    mode=PreemptionMode(input.preemption.mode),
                )
            )

        scheduler_spec = ScalingGroupSchedulerConfigUpdaterSpec(
            scheduler=(
                OptionalState.update(scheduler_value)
                if scheduler_value is not None
                else OptionalState.nop()
            ),
            preemption_config=preemption_config_state,
        )

        updater_spec = ScalingGroupUpdaterSpec(
            status=status_spec,
            metadata=metadata_spec,
            network=network_spec,
            scheduler=scheduler_spec,
        )
        updater = Updater(spec=updater_spec, pk_value=input.resource_group_name)

        action_result = await self._processors.scaling_group.modify_scaling_group.wait_for_complete(
            ModifyScalingGroupAction(updater=updater)
        )
        return UpdateResourceGroupConfigPayloadNode(
            resource_group=self._data_to_detail_node(action_result.scaling_group),
        )

    async def purge(
        self,
        name: str,
    ) -> ResourceGroupNode:
        """Purge a resource group by name.

        Args:
            name: Name of the resource group to purge.

        Returns:
            Pydantic node representing the purged resource group.
        """
        purger = Purger(row_class=ScalingGroupRow, pk_value=name)
        action_result = await self._processors.scaling_group.purge_scaling_group.wait_for_complete(
            PurgeScalingGroupAction(purger=purger)
        )

        return self._data_to_node(action_result.data)

    @staticmethod
    def _data_to_detail_node(data: ScalingGroupData) -> ResourceGroupDetailNode:
        """Convert ScalingGroupData to ResourceGroupDetailNode DTO for GQL layer."""
        return ResourceGroupDetailNode(
            id=data.name,
            name=data.name,
            status=ResourceGroupStatusInfo(
                is_active=data.status.is_active,
                is_public=data.status.is_public,
            ),
            metadata=ResourceGroupMetadataInfo(
                description=data.metadata.description or None,
                created_at=data.metadata.created_at,
            ),
            network=ResourceGroupNetworkConfigInfo(
                wsproxy_addr=data.network.wsproxy_addr or None,
                use_host_network=data.network.use_host_network,
            ),
            scheduler=ResourceGroupSchedulerConfigInfo(
                type=SchedulerTypeDTO(data.scheduler.name.value),
                preemption=PreemptionConfigInfo(
                    preemptible_priority=data.scheduler.options.preemption.preemptible_priority,
                    order=PreemptionOrderDTO(data.scheduler.options.preemption.order.value),
                    mode=PreemptionModeDTO(data.scheduler.options.preemption.mode.value),
                ),
            ),
        )

    @staticmethod
    def _data_to_node(data: ScalingGroupData) -> ResourceGroupNode:
        """Convert ScalingGroupData to ResourceGroupNode DTO.

        Note:
            ``ResourceGroupNode.id`` is set to a sentinel zero-UUID because
            ScalingGroupData (and the underlying ORM row) does not have a UUID
            field — ``name`` is the primary key.  Callers should use ``name``
            as the opaque identifier for resource groups.

            ``domain_name``, ``total_resource_slots``, ``allowed_vfolder_hosts``,
            ``resource_policy``, and ``modified_at`` are also not available in
            ScalingGroupData; they are set to sensible placeholder values.
        """
        return ResourceGroupNode(
            id=_EMPTY_UUID,
            name=data.name,
            domain_name="",
            description=data.metadata.description or None,
            is_active=data.status.is_active,
            total_resource_slots={},
            allowed_vfolder_hosts={},
            integration_id=None,
            resource_policy=None,
            created_at=data.metadata.created_at,
            modified_at=datetime.fromtimestamp(0, tz=UTC),
        )
