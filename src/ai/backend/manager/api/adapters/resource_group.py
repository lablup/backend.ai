"""Resource group adapter bridging DTOs and Processors."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from ai.backend.common.api_handlers import SENTINEL
from ai.backend.common.dto.manager.v2.resource_group.request import (
    AdminSearchResourceGroupsInput,
    CreateResourceGroupInput,
    ResourceGroupFilter,
    ResourceGroupOrder,
    UpdateResourceGroupInput,
)
from ai.backend.common.dto.manager.v2.resource_group.response import (
    CreateResourceGroupPayload,
    ResourceGroupNode,
    UpdateResourceGroupPayload,
)
from ai.backend.common.dto.manager.v2.resource_group.types import (
    ResourceGroupOrderDirection,
    ResourceGroupOrderField,
)
from ai.backend.manager.data.scaling_group.types import ScalingGroupData
from ai.backend.manager.models.scaling_group import ScalingGroupRow
from ai.backend.manager.models.scaling_group.conditions import ScalingGroupConditions
from ai.backend.manager.models.scaling_group.orders import ScalingGroupOrders
from ai.backend.manager.repositories.base import (
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
    ScalingGroupStatusUpdaterSpec,
    ScalingGroupUpdaterSpec,
)
from ai.backend.manager.services.scaling_group.actions.create import CreateScalingGroupAction
from ai.backend.manager.services.scaling_group.actions.list_scaling_groups import (
    SearchScalingGroupsAction,
)
from ai.backend.manager.services.scaling_group.actions.modify import ModifyScalingGroupAction
from ai.backend.manager.services.scaling_group.actions.purge_scaling_group import (
    PurgeScalingGroupAction,
)
from ai.backend.manager.types import OptionalState, TriState

from .base import BaseAdapter
from .pagination import PaginationSpec


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
    """Result of a resource group search containing paginated ScalingGroupData items."""

    items: list[ScalingGroupData]
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
            items=action_result.scaling_groups,
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
