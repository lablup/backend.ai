"""Resource group adapter bridging DTOs and Processors."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal
from typing import TYPE_CHECKING, Any
from uuid import UUID

if TYPE_CHECKING:
    from ai.backend.manager.sokovan.deployment.coordinator import DeploymentCoordinator
    from ai.backend.manager.sokovan.scheduler.coordinator import ScheduleCoordinator

from ai.backend.common.data.entity.domain import DomainID, DomainName
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.resource_group import ResourceGroupID, ResourceGroupName
from ai.backend.common.data.filter_specs import StringMatchSpec
from ai.backend.common.dto.manager.v2.fair_share.types import (
    ResourceSlotEntryInfo,
    ResourceSlotInfo,
    ResourceWeightEntryInfo,
)
from ai.backend.common.dto.manager.v2.resource_group.request import (
    AdminSearchResourceGroupsInput,
    CreateResourceGroupInput,
    PreemptionConfigInputDTO,
    ReplaceResourceGroupDefaultDeploymentOptionsInput,
    ReplaceResourceGroupDefaultSessionOptionsInput,
    ResourceGroupFilter,
    ResourceGroupOrder,
    ResourceWeightEntryInput,
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
    FairShareResourceGroupSpecInfo,
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
    ResourceGroupOrderDirection,
    ResourceGroupOrderField,
    SchedulerTypeDTO,
)
from ai.backend.common.exception import DomainNotFound
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
from ai.backend.manager.data.resource_group.types import (
    PreemptionConfig as DataPreemptionConfig,
)
from ai.backend.manager.data.resource_group.types import (
    ResourceGroupData,
    SchedulerType,
)
from ai.backend.manager.errors.resource import ResourceGroupNotFound
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.condition_utils import combine_conditions_or, negate_conditions
from ai.backend.manager.models.resource_group import ResourceGroupRow
from ai.backend.manager.models.resource_group.conditions import ResourceGroupConditions
from ai.backend.manager.models.resource_group.creators import (
    ResourceGroupCreator,
    ResourceGroupForDomainRelationCreator,
    ResourceGroupForProjectRelationCreator,
)
from ai.backend.manager.models.resource_group.orders import ResourceGroupOrders
from ai.backend.manager.models.resource_group.purgers import (
    ResourceGroupForDomainRelationPurger,
    ResourceGroupForProjectRelationPurger,
)
from ai.backend.manager.models.resource_group.searchers import ResourceGroupSearcher
from ai.backend.manager.models.resource_group.updaters import ResourceGroupUpdater
from ai.backend.manager.models.specs.pagination import NoPagination
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.services.domain.actions.lookup import LookupDomainAction
from ai.backend.manager.services.domain.processors import DomainProcessors
from ai.backend.manager.services.rbac.actions.relation.base import RelationPair
from ai.backend.manager.services.rbac.actions.relation.create import CreateRelationAction
from ai.backend.manager.services.rbac.actions.relation.purge import PurgeRelationAction
from ai.backend.manager.services.rbac.processors import RbacProcessors
from ai.backend.manager.services.resource_group.actions.bulk_get import (
    BulkGetResourceGroupsAction,
)
from ai.backend.manager.services.resource_group.actions.bulk_lookup import (
    BulkLookupResourceGroupsAction,
)
from ai.backend.manager.services.resource_group.actions.create import CreateResourceGroupAction
from ai.backend.manager.services.resource_group.actions.get_allowed_domains_for_rg import (
    GetAllowedDomainsForResourceGroupAction,
)
from ai.backend.manager.services.resource_group.actions.get_allowed_projects_for_rg import (
    GetAllowedProjectsForResourceGroupAction,
)
from ai.backend.manager.services.resource_group.actions.get_allowed_rgs_for_domain import (
    GetAllowedResourceGroupsForDomainAction,
)
from ai.backend.manager.services.resource_group.actions.get_allowed_rgs_for_project import (
    GetAllowedResourceGroupsForProjectAction,
)
from ai.backend.manager.services.resource_group.actions.get_resource_info import (
    GetResourceInfoAction,
)
from ai.backend.manager.services.resource_group.actions.list_resource_groups import (
    SearchResourceGroupsAction,
)
from ai.backend.manager.services.resource_group.actions.lookup import LookupResourceGroupAction
from ai.backend.manager.services.resource_group.actions.purge_resource_group import (
    PurgeResourceGroupAction,
)
from ai.backend.manager.services.resource_group.actions.replace_default_deployment_options import (
    ReplaceDefaultDeploymentOptionsAction,
)
from ai.backend.manager.services.resource_group.actions.replace_default_session_options import (
    ReplaceDefaultSessionOptionsAction,
)
from ai.backend.manager.services.resource_group.actions.resolve_resource_group_ids_by_names import (
    ResolveResourceGroupIDsByNamesAction,
)
from ai.backend.manager.services.resource_group.actions.scoped_search import (
    DomainResourceGroupScopeItem,
    ProjectResourceGroupScopeItem,
    ResourceGroupScopeItem,
    ScopedSearchResourceGroupsAction,
)
from ai.backend.manager.services.resource_group.actions.update import UpdateResourceGroupAction
from ai.backend.manager.services.resource_group.actions.update_fair_share_spec import (
    ResourceWeightInput,
    UpdateFairShareSpecAction,
)
from ai.backend.manager.services.resource_group.processors import ResourceGroupProcessors
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
        forward_order=ResourceGroupOrders.created_at(ascending=False),
        backward_order=ResourceGroupOrders.created_at(ascending=True),
        forward_condition_factory=ResourceGroupConditions.by_cursor_forward,
        backward_condition_factory=ResourceGroupConditions.by_cursor_backward,
        tiebreaker_order=ResourceGroupRow.name.asc(),
    )


def _resource_weights_to_domain(
    entries: Sequence[ResourceWeightEntryInput],
) -> list[ResourceWeightInput]:
    return [
        ResourceWeightInput(resource_type=entry.resource_type, weight=entry.weight)
        for entry in entries
    ]


def _preemption_input_to_domain(preemption: PreemptionConfigInputDTO) -> DataPreemptionConfig:
    return DataPreemptionConfig(
        enabled=preemption.enabled,
        preemptible_priority=preemption.preemptible_priority,
        order=PreemptionOrder(preemption.order),
        mode=PreemptionMode(preemption.mode),
        preemption_min_runtime=timedelta(seconds=preemption.preemption_min_runtime),
        victim_scope=preemption.victim_scope,
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

    Note: ResourceGroupData uses ``name`` (str) as primary key, while the
        exposed ``id`` field carries the resource group UUID.
    """

    _resource_group: ResourceGroupProcessors
    _rbac: RbacProcessors
    _domain: DomainProcessors
    _deployment_coordinator: DeploymentCoordinator
    _schedule_coordinator: ScheduleCoordinator

    def __init__(
        self,
        resource_group: ResourceGroupProcessors,
        rbac: RbacProcessors,
        domain: DomainProcessors,
        deployment_coordinator: DeploymentCoordinator,
        schedule_coordinator: ScheduleCoordinator,
    ) -> None:
        self._resource_group = resource_group
        self._rbac = rbac
        self._domain = domain
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
    ) -> list[ResourceGroupDetailNode | Exception | None]:
        """Batch load resource groups by name for DataLoader use.

        One answer per name in the given order: the node, ``None`` for a name matching
        no resource group, and the denial for one the caller may not read.
        """
        if not names:
            return []
        keys = [ResourceGroupName(name) for name in names]
        lookup = await self._resource_group.bulk_lookup.run(
            BulkLookupResourceGroupsAction(names=keys)
        )
        ids = [lookup.resolved[key] for key in keys if key in lookup.resolved]
        got = await self._resource_group.bulk_get.run(BulkGetResourceGroupsAction(ids=ids))
        groups = got.values()
        errors = got.errors()
        nodes: list[ResourceGroupDetailNode | Exception | None] = []
        for key in keys:
            resource_group_id = lookup.resolved.get(key)
            if resource_group_id is None:
                nodes.append(None)
                continue
            data = groups.get(resource_group_id)
            if data is None:
                nodes.append(self.batch_load_failure(errors.get(resource_group_id)))
                continue
            nodes.append(self._data_to_detail_node(data))
        return nodes

    async def batch_load_by_ids(
        self, ids: Sequence[ResourceGroupID]
    ) -> list[ResourceGroupDetailNode | Exception | None]:
        """Batch load resource groups by UUID for DataLoader use, checked per resource group."""
        if not ids:
            return []
        result = await self._resource_group.bulk_get.run(BulkGetResourceGroupsAction(ids=list(ids)))
        return [
            self._data_to_detail_node(item.value)
            if item.value is not None
            else self.batch_load_failure(item.error)
            for item in result.items
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
        action_result = await self._resource_group.search_resource_groups.run(
            SearchResourceGroupsAction(querier=querier)
        )
        return ResourceGroupSearchPayload(
            items=[self._data_to_detail_node(sg) for sg in action_result.resource_groups],
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
                contains_factory=ResourceGroupConditions.by_name_contains,
                equals_factory=ResourceGroupConditions.by_name_equals,
                starts_with_factory=ResourceGroupConditions.by_name_starts_with,
                ends_with_factory=ResourceGroupConditions.by_name_ends_with,
                in_factory=ResourceGroupConditions.by_name_in,
            )
            if cond:
                conditions.append(cond)
        if filter_.description:
            cond = self.convert_string_filter(
                filter_.description,
                contains_factory=ResourceGroupConditions.by_description_contains,
                equals_factory=ResourceGroupConditions.by_description_equals,
                starts_with_factory=ResourceGroupConditions.by_description_starts_with,
                ends_with_factory=ResourceGroupConditions.by_description_ends_with,
                in_factory=ResourceGroupConditions.by_description_in,
            )
            if cond:
                conditions.append(cond)
        if filter_.is_active is not None:
            conditions.append(ResourceGroupConditions.by_is_active(filter_.is_active))
        if filter_.is_public is not None:
            conditions.append(ResourceGroupConditions.by_is_public(filter_.is_public))
        if filter_.is_default is not None:
            conditions.append(ResourceGroupConditions.by_is_default(filter_.is_default))
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
                    result.append(ResourceGroupOrders.name(ascending))
                case ResourceGroupOrderField.CREATED_AT:
                    result.append(ResourceGroupOrders.created_at(ascending))
                case ResourceGroupOrderField.IS_ACTIVE:
                    result.append(ResourceGroupOrders.is_active(ascending))
        return result

    async def get(self, name: str) -> ResourceGroupDetailNode:
        """Retrieve a single resource group by name."""
        results = await self.batch_load_by_names([name])
        match results[0]:
            case None:
                raise ResourceGroupNotFound(f"Resource group '{name}' not found.")
            case Exception() as denial:
                raise denial
            case node:
                return node

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
        creator = ResourceGroupCreator(
            name=input.name,
            # ResourceGroupCreator requires driver and scheduler fields
            # which are not exposed in CreateResourceGroupInput.
            # Default to "static" driver and "fifo" scheduler as reasonable defaults.
            driver="static",
            scheduler="fifo",
            description=input.description,
            is_active=True,
            is_default=input.is_default,
        )
        action_result = await self._resource_group.create_resource_group.run(
            CreateResourceGroupAction(creator=creator)
        )

        return CreateResourceGroupPayload(
            resource_group=self._data_to_detail_node(action_result.resource_group),
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
        updater = ResourceGroupUpdater(
            resource_group_id=await self._resolve_resource_group_id(name),
            is_active=OptionalState.from_unset(input.is_active),
            is_default=OptionalState.from_unset(input.is_default),
            description=TriState.from_unset(input.description),
        )
        action_result = await self._resource_group.update_resource_group.run(
            UpdateResourceGroupAction(resource_group_id=updater.resource_group_id, updater=updater)
        )

        return UpdateResourceGroupPayload(
            resource_group=self._data_to_detail_node(action_result.resource_group),
        )

    async def get_resource_info(self, resource_group: str) -> ResourceInfoNode:
        """Get resource information for a scaling group.

        Args:
            scaling_group: Name of the scaling group.

        Returns:
            ResourceInfoNode DTO with capacity, used, and free resource metrics.
            Quantities are normalized (trailing zeros removed, no scientific notation).
        """
        action_result = await self._resource_group.get_resource_info.run(
            GetResourceInfoAction(
                resource_group_id=await self._resolve_resource_group_id(resource_group),
                resource_group=resource_group,
            )
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
    ) -> FairShareResourceGroupSpecInfo:
        """Get fair share spec merged with capacity resource weights for a resource group.

        Merges the resource group's fair share spec with the current capacity
        so that resource_weights contains entries for all available resource types.
        Missing resource types use default_weight.

        Returns:
            FairShareResourceGroupSpecInfo DTO with merged resource weights and
            uses_default indicators per resource type.
        """
        name_spec = StringMatchSpec(
            value=resource_group,
            case_insensitive=False,
            negated=False,
        )
        querier = BatchQuerier(
            pagination=NoPagination(),
            conditions=[ResourceGroupConditions.by_name_equals(name_spec)],
        )
        search_result = await self._resource_group.search_resource_groups.run(
            SearchResourceGroupsAction(querier=querier)
        )
        if not search_result.resource_groups:
            raise ResourceGroupNotFound(resource_group)
        sg_data = search_result.resource_groups[0]

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

        return FairShareResourceGroupSpecInfo(
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
        weight_entries = OptionalState.from_unset(input.resource_weights).optional_value()
        resource_weights = (
            _resource_weights_to_domain(weight_entries) if weight_entries is not None else None
        )
        action_result = await self._resource_group.update_fair_share_spec.run(
            UpdateFairShareSpecAction(
                resource_group_id=await self._resolve_resource_group_id(input.resource_group_name),
                resource_group=input.resource_group_name,
                half_life_days=OptionalState.from_unset(input.half_life_days).optional_value(),
                lookback_days=OptionalState.from_unset(input.lookback_days).optional_value(),
                decay_unit_days=OptionalState.from_unset(input.decay_unit_days).optional_value(),
                default_weight=OptionalState.from_unset(input.default_weight).optional_value(),
                resource_weights=resource_weights,
            )
        )
        return UpdateResourceGroupFairShareSpecPayloadNode(
            resource_group=self._data_to_detail_node(action_result.resource_group),
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
        updater = ResourceGroupUpdater(
            resource_group_id=await self._resolve_resource_group_id(input.resource_group_name),
            is_active=OptionalState.from_unset(input.is_active),
            is_public=OptionalState.from_unset(input.is_public),
            is_default=OptionalState.from_unset(input.is_default),
            description=TriState.from_unset(input.description),
            wsproxy_addr=TriState.from_unset(input.app_proxy_addr),
            wsproxy_api_token=TriState.from_unset(input.appproxy_api_token),
            use_host_network=OptionalState.from_unset(input.use_host_network),
            scheduler=OptionalState.from_unset(input.scheduler_type).map(
                lambda v: SchedulerType(v).value
            ),
            preemption_config=OptionalState.from_unset(input.preemption).map(
                _preemption_input_to_domain
            ),
        )

        action_result = await self._resource_group.update_resource_group.run(
            UpdateResourceGroupAction(
                resource_group_id=updater.resource_group_id,
                updater=updater,
            )
        )
        return UpdateResourceGroupConfigPayloadNode(
            resource_group=self._data_to_detail_node(action_result.resource_group),
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
        action_result = await self._resource_group.purge_resource_group.run(
            PurgeResourceGroupAction(resource_group_id=await self._resolve_resource_group_id(name))
        )

        return self._data_to_detail_node(action_result.data)

    # Allow / Disallow operations

    async def _resolve_domain_id(self, domain_name: str) -> DomainID:
        """Resolve a domain name to its row id at the API boundary."""
        result = await self._domain.lookup.run(LookupDomainAction(name=DomainName(domain_name)))
        return result.entity_id()

    async def _resolve_resource_group_id(self, name: str) -> ResourceGroupID:
        """Resolve a resource group name to its row ID at the API boundary."""
        result = await self._resource_group.lookup.run(
            LookupResourceGroupAction(name=ResourceGroupName(name))
        )
        return result.entity_id()

    async def _resolve_allowed_resource_group_ids(
        self,
        add: list[str],
        remove: list[str],
    ) -> tuple[list[ResourceGroupID], list[ResourceGroupID]]:
        """Resolve allow-list names to row IDs at the API boundary.

        Names to add must exist; unknown names to remove are skipped.
        """
        names = [ResourceGroupName(name) for name in {*add, *remove}]
        if not names:
            return [], []
        result = await self._resource_group.resolve_resource_group_ids_by_names.run(
            ResolveResourceGroupIDsByNamesAction(names=names)
        )
        ids_by_name = result.ids_by_name
        missing = sorted(name for name in add if name not in ids_by_name)
        if missing:
            raise ResourceGroupNotFound(", ".join(missing))
        add_ids = [ids_by_name[ResourceGroupName(name)] for name in add]
        remove_ids = [
            ids_by_name[ResourceGroupName(name)] for name in remove if name in ids_by_name
        ]
        return add_ids, remove_ids

    async def _link_resource_groups_to_domain(
        self, domain_id: DomainID, resource_group_ids: list[ResourceGroupID]
    ) -> None:
        """Link the domain to every named resource group in one run. A pair already
        linked is left as it stands: naming one twice is not an error to the caller."""
        if not resource_group_ids:
            return
        await self._rbac.create_relation.run(
            CreateRelationAction(
                pairs=[
                    RelationPair(scope=domain_id, target=resource_group_id)
                    for resource_group_id in resource_group_ids
                ],
                creator=ResourceGroupForDomainRelationCreator(),
            )
        )

    async def _unlink_resource_groups_from_domain(
        self, domain_id: DomainID, resource_group_ids: list[ResourceGroupID]
    ) -> None:
        if not resource_group_ids:
            return
        await self._rbac.purge_relation.run(
            PurgeRelationAction(
                pairs=[
                    RelationPair(scope=domain_id, target=resource_group_id)
                    for resource_group_id in resource_group_ids
                ],
                purger=ResourceGroupForDomainRelationPurger(),
            )
        )

    async def _link_resource_groups_to_project(
        self, project_id: ProjectID, resource_group_ids: list[ResourceGroupID]
    ) -> None:
        """Link the project to every named resource group in one run. A pair already
        linked is left as it stands: naming one twice is not an error to the caller."""
        if not resource_group_ids:
            return
        await self._rbac.create_relation.run(
            CreateRelationAction(
                pairs=[
                    RelationPair(scope=project_id, target=resource_group_id)
                    for resource_group_id in resource_group_ids
                ],
                creator=ResourceGroupForProjectRelationCreator(),
            )
        )

    async def _unlink_resource_groups_from_project(
        self, project_id: ProjectID, resource_group_ids: list[ResourceGroupID]
    ) -> None:
        if not resource_group_ids:
            return
        await self._rbac.purge_relation.run(
            PurgeRelationAction(
                pairs=[
                    RelationPair(scope=project_id, target=resource_group_id)
                    for resource_group_id in resource_group_ids
                ],
                purger=ResourceGroupForProjectRelationPurger(),
            )
        )

    async def _link_domains_to_resource_group(
        self, resource_group_id: ResourceGroupID, domain_ids: list[DomainID]
    ) -> None:
        """The same link read from the resource group's side, in one run."""
        if not domain_ids:
            return
        await self._rbac.create_relation.run(
            CreateRelationAction(
                pairs=[
                    RelationPair(scope=domain_id, target=resource_group_id)
                    for domain_id in domain_ids
                ],
                creator=ResourceGroupForDomainRelationCreator(),
            )
        )

    async def _unlink_domains_from_resource_group(
        self, resource_group_id: ResourceGroupID, domain_ids: list[DomainID]
    ) -> None:
        if not domain_ids:
            return
        await self._rbac.purge_relation.run(
            PurgeRelationAction(
                pairs=[
                    RelationPair(scope=domain_id, target=resource_group_id)
                    for domain_id in domain_ids
                ],
                purger=ResourceGroupForDomainRelationPurger(),
            )
        )

    async def _link_projects_to_resource_group(
        self, resource_group_id: ResourceGroupID, project_ids: list[ProjectID]
    ) -> None:
        """The same link read from the resource group's side, in one run."""
        if not project_ids:
            return
        await self._rbac.create_relation.run(
            CreateRelationAction(
                pairs=[
                    RelationPair(scope=project_id, target=resource_group_id)
                    for project_id in project_ids
                ],
                creator=ResourceGroupForProjectRelationCreator(),
            )
        )

    async def _unlink_projects_from_resource_group(
        self, resource_group_id: ResourceGroupID, project_ids: list[ProjectID]
    ) -> None:
        if not project_ids:
            return
        await self._rbac.purge_relation.run(
            PurgeRelationAction(
                pairs=[
                    RelationPair(scope=project_id, target=resource_group_id)
                    for project_id in project_ids
                ],
                purger=ResourceGroupForProjectRelationPurger(),
            )
        )

    async def _resolve_allowed_domain_ids(
        self,
        add: list[str],
        remove: list[str],
    ) -> tuple[list[DomainID], list[DomainID]]:
        """Resolve allow-list domain names to row ids at the API boundary.

        Names to add must exist; unknown names to remove are skipped.
        """
        add_ids = [await self._resolve_domain_id(name) for name in add]
        remove_ids: list[DomainID] = []
        for name in remove:
            try:
                remove_ids.append(await self._resolve_domain_id(name))
            except DomainNotFound:
                continue
        return add_ids, remove_ids

    async def update_allowed_resource_groups_for_domain(
        self,
        input: UpdateAllowedResourceGroupsForDomainInput,
    ) -> AllowedResourceGroupsPayload:
        """Add and remove the resource groups a domain may schedule on."""
        add_ids, remove_ids = await self._resolve_allowed_resource_group_ids(
            input.add or [], input.remove or []
        )
        domain_id = await self._resolve_domain_id(input.domain_name)
        await self._unlink_resource_groups_from_domain(domain_id, remove_ids)
        await self._link_resource_groups_to_domain(domain_id, add_ids)
        result = await self._resource_group.get_allowed_rgs_for_domain.run(
            GetAllowedResourceGroupsForDomainAction(domain_id=domain_id)
        )
        return AllowedResourceGroupsPayload(items=result.items)

    async def update_allowed_resource_groups_for_project(
        self,
        input: UpdateAllowedResourceGroupsForProjectInput,
    ) -> AllowedResourceGroupsPayload:
        """Add and remove the resource groups a project may schedule on."""
        add_ids, remove_ids = await self._resolve_allowed_resource_group_ids(
            input.add or [], input.remove or []
        )
        project_id = ProjectID(input.project_id)
        await self._unlink_resource_groups_from_project(project_id, remove_ids)
        await self._link_resource_groups_to_project(project_id, add_ids)
        result = await self._resource_group.get_allowed_rgs_for_project.run(
            GetAllowedResourceGroupsForProjectAction(project_id=project_id)
        )
        return AllowedResourceGroupsPayload(items=result.items)

    async def update_allowed_domains_for_resource_group(
        self,
        input: UpdateAllowedDomainsForResourceGroupInput,
    ) -> AllowedDomainsPayload:
        """Add and remove the domains a resource group may be scheduled on from."""
        resource_group_id = await self._resolve_resource_group_id(input.resource_group_name)
        add_ids, remove_ids = await self._resolve_allowed_domain_ids(
            input.add or [], input.remove or []
        )
        await self._unlink_domains_from_resource_group(resource_group_id, remove_ids)
        await self._link_domains_to_resource_group(resource_group_id, add_ids)
        result = await self._resource_group.get_allowed_domains_for_rg.run(
            GetAllowedDomainsForResourceGroupAction(resource_group_id=resource_group_id)
        )
        return AllowedDomainsPayload(items=result.items)

    async def update_allowed_projects_for_resource_group(
        self,
        input: UpdateAllowedProjectsForResourceGroupInput,
    ) -> AllowedProjectsPayload:
        """Add and remove the projects a resource group may be scheduled on from."""
        resource_group_id = await self._resolve_resource_group_id(input.resource_group_name)
        await self._unlink_projects_from_resource_group(
            resource_group_id, [ProjectID(raw) for raw in input.remove or []]
        )
        await self._link_projects_to_resource_group(
            resource_group_id, [ProjectID(raw) for raw in input.add or []]
        )
        result = await self._resource_group.get_allowed_projects_for_rg.run(
            GetAllowedProjectsForResourceGroupAction(resource_group_id=resource_group_id)
        )
        return AllowedProjectsPayload(items=result.items)

    async def _scoped_resource_group_names(self, item: ResourceGroupScopeItem) -> list[str]:
        """Read the resource groups one scope reaches, by name."""
        result = await self._resource_group.scoped_search_resource_groups.run(
            ScopedSearchResourceGroupsAction(
                items=[item],
                searcher=ResourceGroupSearcher(
                    pagination=NoPagination(),
                    orders=[ResourceGroupOrders.name()],
                ),
            )
        )
        return [data.name for data in result.items]

    async def get_allowed_resource_groups_for_domain(
        self,
        domain_name: str,
    ) -> AllowedResourceGroupsPayload:
        """Get allowed resource groups for a domain."""
        return AllowedResourceGroupsPayload(
            items=await self._scoped_resource_group_names(
                DomainResourceGroupScopeItem(domain_id=await self._resolve_domain_id(domain_name))
            )
        )

    async def get_allowed_resource_groups_for_project(
        self,
        project_id: UUID,
    ) -> AllowedResourceGroupsPayload:
        """Get allowed resource groups for a project."""
        return AllowedResourceGroupsPayload(
            items=await self._scoped_resource_group_names(
                ProjectResourceGroupScopeItem(project_id=ProjectID(project_id))
            )
        )

    async def get_allowed_domains_for_resource_group(
        self,
        resource_group_name: str,
    ) -> AllowedDomainsPayload:
        """Get allowed domains for a resource group."""
        resource_group_id = await self._resolve_resource_group_id(resource_group_name)
        result = await self._resource_group.get_allowed_domains_for_rg.run(
            GetAllowedDomainsForResourceGroupAction(resource_group_id=resource_group_id)
        )
        return AllowedDomainsPayload(items=result.items)

    async def get_allowed_projects_for_resource_group(
        self,
        resource_group_name: str,
    ) -> AllowedProjectsPayload:
        """Get allowed projects for a resource group."""
        resource_group_id = await self._resolve_resource_group_id(resource_group_name)
        result = await self._resource_group.get_allowed_projects_for_rg.run(
            GetAllowedProjectsForResourceGroupAction(resource_group_id=resource_group_id)
        )
        return AllowedProjectsPayload(items=result.items)

    @staticmethod
    def _data_to_detail_node(data: ResourceGroupData) -> ResourceGroupDetailNode:
        """Convert ResourceGroupData to ResourceGroupDetailNode DTO for GQL layer."""
        return ResourceGroupDetailNode(
            id=data.id,
            name=data.name,
            status=ResourceGroupStatusInfo(
                is_active=data.status.is_active,
                is_public=data.status.is_public,
                is_default=data.status.is_default,
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
                    enabled=data.scheduler.options.preemption.enabled,
                    preemptible_priority=data.scheduler.options.preemption.preemptible_priority,
                    order=data.scheduler.options.preemption.order,
                    mode=PreemptionModeDTO(data.scheduler.options.preemption.mode.value),
                    preemption_min_runtime=data.scheduler.options.preemption.preemption_min_runtime.total_seconds(),
                    victim_scope=data.scheduler.options.preemption.victim_scope,
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
        action_result = await self._resource_group.replace_default_deployment_options.run(
            ReplaceDefaultDeploymentOptionsAction(
                resource_group_id=await self._resolve_resource_group_id(name),
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
        action_result = await self._resource_group.replace_default_session_options.run(
            ReplaceDefaultSessionOptionsAction(
                resource_group_id=await self._resolve_resource_group_id(name),
                resource_group=name,
                options=options,
            )
        )
        return ReplaceResourceGroupDefaultSessionOptionsPayload(
            resource_group_name=action_result.resource_group,
            default_session_options=default_session_options_to_info(action_result.options),
        )
