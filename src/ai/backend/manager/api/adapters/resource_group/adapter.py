"""Resource group adapter bridging DTOs and Processors."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING, Any
from uuid import UUID

if TYPE_CHECKING:
    from ai.backend.manager.services.processors import Processors
    from ai.backend.manager.sokovan.deployment.coordinator import DeploymentCoordinator
    from ai.backend.manager.sokovan.scheduler.coordinator import ScheduleCoordinator

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
    ReplaceResourceGroupDefaultDeploymentOptionsInput,
    ReplaceResourceGroupDefaultSessionOptionsInput,
    ResourceGroupFilter,
    ResourceGroupOrder,
    UpdateAllowedDomainsForResourceGroupInput,
    UpdateAllowedProjectsForResourceGroupInput,
    UpdateAllowedResourceGroupsForDomainInput,
    UpdateAllowedResourceGroupsForProjectInput,
    UpdateResourceGroupConfigInput,
    UpdateResourceGroupFairShareSpecInput,
    UpdateResourceGroupInput,
)
from ai.backend.common.dto.manager.v2.resource_group.response import (
    AllowedDomainsPayload,
    AllowedProjectsPayload,
    AllowedResourceGroupsPayload,
    CreateResourceGroupPayload,
    FairShareScalingGroupSpecInfo,
    PreemptionConfigInfo,
    ReplaceResourceGroupDefaultDeploymentOptionsPayload,
    ReplaceResourceGroupDefaultSessionOptionsPayload,
    ResourceGroupDetailNode,
    ResourceGroupMetadataInfo,
    ResourceGroupNetworkConfigInfo,
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
from ai.backend.common.identifier.resource_group import ResourceGroupName
from ai.backend.common.types import PreemptionMode, PreemptionOrder, SlotQuantity
from ai.backend.manager.api.adapter_options.deployment.options import (
    deployment_options_from_input,
    deployment_options_to_info,
)
from ai.backend.manager.api.adapter_options.pagination.pagination import PaginationSpec
from ai.backend.manager.api.adapter_options.session.options import (
    default_session_options_from_input,
    default_session_options_to_info,
)
from ai.backend.manager.api.adapters.base import BaseAdapter
from ai.backend.manager.data.scaling_group.types import (
    PreemptionConfig as DataPreemptionConfig,
)
from ai.backend.manager.data.scaling_group.types import (
    ScalingGroupData,
    SchedulerType,
)
from ai.backend.manager.errors.resource import ScalingGroupNotFound
from ai.backend.manager.models.query_types import QueryCondition
from ai.backend.manager.models.scaling_group import ScalingGroupRow
from ai.backend.manager.models.scaling_group.conditions import ScalingGroupConditions
from ai.backend.manager.models.scaling_group.orders import ScalingGroupOrders
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    NoPagination,
    OffsetPagination,
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
from ai.backend.manager.services.scaling_group.actions.get_allowed_domains_for_rg import (
    GetAllowedDomainsForResourceGroupAction,
)
from ai.backend.manager.services.scaling_group.actions.get_allowed_projects_for_rg import (
    GetAllowedProjectsForResourceGroupAction,
)
from ai.backend.manager.services.scaling_group.actions.get_allowed_rgs_for_domain import (
    GetAllowedResourceGroupsForDomainAction,
)
from ai.backend.manager.services.scaling_group.actions.get_allowed_rgs_for_project import (
    GetAllowedResourceGroupsForProjectAction,
)
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
from ai.backend.manager.services.scaling_group.actions.replace_default_deployment_options import (
    ReplaceDefaultDeploymentOptionsAction,
)
from ai.backend.manager.services.scaling_group.actions.replace_default_session_options import (
    ReplaceDefaultSessionOptionsAction,
)
from ai.backend.manager.services.scaling_group.actions.update_allowed_domains_for_rg import (
    UpdateAllowedDomainsForResourceGroupAction,
)
from ai.backend.manager.services.scaling_group.actions.update_allowed_projects_for_rg import (
    UpdateAllowedProjectsForResourceGroupAction,
)
from ai.backend.manager.services.scaling_group.actions.update_allowed_rgs_for_domain import (
    UpdateAllowedResourceGroupsForDomainAction,
)
from ai.backend.manager.services.scaling_group.actions.update_allowed_rgs_for_project import (
    UpdateAllowedResourceGroupsForProjectAction,
)
from ai.backend.manager.services.scaling_group.actions.update_fair_share_spec import (
    ResourceWeightInput,
    UpdateFairShareSpecAction,
)
from ai.backend.manager.types import OptionalState, TriState


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


class ResourceGroupAdapter(BaseAdapter):
    """Adapter for resource group (scaling group) operations.

    Bridges CreateResourceGroupInput / UpdateResourceGroupInput DTOs to
    ScalingGroup Processor actions and converts results back to Pydantic DTOs.

    Note: ScalingGroupData uses ``name`` (str) as primary key.  Callers that
        need an opaque identifier should use the ``name`` field instead.
    """

    def __init__(
        self,
        processors: Processors,
        deployment_coordinator: DeploymentCoordinator,
        schedule_coordinator: ScheduleCoordinator,
    ) -> None:
        super().__init__(processors)
        # ``deployment_coordinator`` is the authoritative source for the
        # live set of registered handler names; we consult it when
        # validating
        # ``default_deployment_options.handler_options.by_handler`` keys
        # so an unknown handler surfaces as a 400 instead of a silently
        # stored, never-dispatched entry.
        self._deployment_coordinator = deployment_coordinator
        # ``schedule_coordinator`` plays the same role for the session
        # side — ``default_session_options.handler_options.by_handler`` keys
        # are validated against the live set of session lifecycle
        # handlers.
        self._schedule_coordinator = schedule_coordinator

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
                in_factory=ScalingGroupConditions.by_name_in,
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
                in_factory=ScalingGroupConditions.by_description_in,
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

    async def get(self, name: str) -> ResourceGroupDetailNode:
        """Retrieve a single resource group by name."""
        results = await self.batch_load_by_names([name])
        if results[0] is None:
            raise ScalingGroupNotFound(f"Resource group '{name}' not found.")
        return results[0]

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
            resource_group=self._data_to_detail_node(action_result.scaling_group),
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
            resource_group=self._data_to_detail_node(action_result.scaling_group),
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
    ) -> ResourceGroupDetailNode:
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

        return self._data_to_detail_node(action_result.data)

    # Allow / Disallow operations

    async def update_allowed_resource_groups_for_domain(
        self,
        input: UpdateAllowedResourceGroupsForDomainInput,
    ) -> AllowedResourceGroupsPayload:
        """Atomically add/remove allowed resource groups for a domain."""
        result = (
            await self._processors.scaling_group.update_allowed_rgs_for_domain.wait_for_complete(
                UpdateAllowedResourceGroupsForDomainAction(
                    domain_name=input.domain_name,
                    add=input.add or [],
                    remove=input.remove or [],
                )
            )
        )
        return AllowedResourceGroupsPayload(items=result.allowed_resource_groups)

    async def update_allowed_resource_groups_for_project(
        self,
        input: UpdateAllowedResourceGroupsForProjectInput,
    ) -> AllowedResourceGroupsPayload:
        """Atomically add/remove allowed resource groups for a project."""
        result = (
            await self._processors.scaling_group.update_allowed_rgs_for_project.wait_for_complete(
                UpdateAllowedResourceGroupsForProjectAction(
                    project_id=input.project_id,
                    add=input.add or [],
                    remove=input.remove or [],
                )
            )
        )
        return AllowedResourceGroupsPayload(items=result.allowed_resource_groups)

    async def update_allowed_domains_for_resource_group(
        self,
        input: UpdateAllowedDomainsForResourceGroupInput,
    ) -> AllowedDomainsPayload:
        """Atomically add/remove allowed domains for a resource group."""
        result = (
            await self._processors.scaling_group.update_allowed_domains_for_rg.wait_for_complete(
                UpdateAllowedDomainsForResourceGroupAction(
                    resource_group_name=input.resource_group_name,
                    add=input.add or [],
                    remove=input.remove or [],
                )
            )
        )
        return AllowedDomainsPayload(items=result.allowed_domains)

    async def update_allowed_projects_for_resource_group(
        self,
        input: UpdateAllowedProjectsForResourceGroupInput,
    ) -> AllowedProjectsPayload:
        """Atomically add/remove allowed projects for a resource group."""
        result = (
            await self._processors.scaling_group.update_allowed_projects_for_rg.wait_for_complete(
                UpdateAllowedProjectsForResourceGroupAction(
                    resource_group_name=input.resource_group_name,
                    add=input.add or [],
                    remove=input.remove or [],
                )
            )
        )
        return AllowedProjectsPayload(items=result.allowed_projects)

    async def get_allowed_resource_groups_for_domain(
        self,
        domain_name: str,
    ) -> AllowedResourceGroupsPayload:
        """Get allowed resource groups for a domain."""
        result = await self._processors.scaling_group.get_allowed_rgs_for_domain.wait_for_complete(
            GetAllowedResourceGroupsForDomainAction(domain_name=domain_name)
        )
        return AllowedResourceGroupsPayload(items=result.items)

    async def get_allowed_resource_groups_for_project(
        self,
        project_id: UUID,
    ) -> AllowedResourceGroupsPayload:
        """Get allowed resource groups for a project."""
        result = await self._processors.scaling_group.get_allowed_rgs_for_project.wait_for_complete(
            GetAllowedResourceGroupsForProjectAction(project_id=project_id)
        )
        return AllowedResourceGroupsPayload(items=result.items)

    async def get_allowed_domains_for_resource_group(
        self,
        resource_group_name: str,
    ) -> AllowedDomainsPayload:
        """Get allowed domains for a resource group."""
        result = await self._processors.scaling_group.get_allowed_domains_for_rg.wait_for_complete(
            GetAllowedDomainsForResourceGroupAction(resource_group_name=resource_group_name)
        )
        return AllowedDomainsPayload(items=result.items)

    async def get_allowed_projects_for_resource_group(
        self,
        resource_group_name: str,
    ) -> AllowedProjectsPayload:
        """Get allowed projects for a resource group."""
        result = await self._processors.scaling_group.get_allowed_projects_for_rg.wait_for_complete(
            GetAllowedProjectsForResourceGroupAction(resource_group_name=resource_group_name)
        )
        return AllowedProjectsPayload(items=result.items)

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
            default_deployment_options=deployment_options_to_info(data.default_deployment_options),
            default_session_options=default_session_options_to_info(data.default_session_options),
        )

    async def admin_replace_default_deployment_options(
        self,
        name: ResourceGroupName,
        input: ReplaceResourceGroupDefaultDeploymentOptionsInput,
    ) -> ReplaceResourceGroupDefaultDeploymentOptionsPayload:
        """Fully replace a resource group's ``default_deployment_options``.

        Admin-only. The DTO payload is converted to the domain
        :class:`DeploymentOptions` (duplicate or unknown handler names
        are rejected against the coordinator's live registration), the
        :class:`ReplaceDefaultDeploymentOptionsAction` is dispatched, and
        only the refreshed options surface is returned (the repository
        path uses ``UPDATE ... RETURNING`` and does not re-read the
        surrounding scaling group node).
        """
        options = deployment_options_from_input(
            input.options,
            valid_handler_names=frozenset(
                h.name() for h in self._deployment_coordinator.registered_handlers()
            ),
        )
        action_result = await self._processors.scaling_group.replace_default_deployment_options.wait_for_complete(
            ReplaceDefaultDeploymentOptionsAction(
                resource_group=name,
                options=options,
            )
        )
        return ReplaceResourceGroupDefaultDeploymentOptionsPayload(
            resource_group_name=action_result.resource_group,
            default_deployment_options=deployment_options_to_info(action_result.options),
        )

    async def admin_replace_default_session_options(
        self,
        name: ResourceGroupName,
        input: ReplaceResourceGroupDefaultSessionOptionsInput,
    ) -> ReplaceResourceGroupDefaultSessionOptionsPayload:
        """Fully replace a resource group's ``default_session_options``.

        Admin-only. Mirror of ``admin_replace_default_deployment_options``:
        the DTO payload is converted to the domain
        :class:`DefaultSessionOptions` (duplicate or unknown handler
        names are rejected against the schedule coordinator's live
        registration), the :class:`ReplaceDefaultSessionOptionsAction`
        is dispatched, and only the refreshed options surface is
        returned.
        """
        options = default_session_options_from_input(
            input.options,
            valid_handler_names=frozenset(
                h.name() for h in self._schedule_coordinator.registered_lifecycle_handlers()
            ),
        )
        action_result = (
            await self._processors.scaling_group.replace_default_session_options.wait_for_complete(
                ReplaceDefaultSessionOptionsAction(
                    resource_group=name,
                    options=options,
                )
            )
        )
        return ReplaceResourceGroupDefaultSessionOptionsPayload(
            resource_group_name=action_result.resource_group,
            default_session_options=default_session_options_to_info(action_result.options),
        )
