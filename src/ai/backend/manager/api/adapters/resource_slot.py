"""Resource slot adapter bridging DTOs and Processors."""

from __future__ import annotations

from ai.backend.common.dto.manager.query import StringFilter, UUIDFilter
from ai.backend.common.dto.manager.v2.resource_slot.request import (
    AdminSearchAgentResourcesInput,
    AdminSearchResourceAllocationsInput,
    AdminSearchResourceSlotTypesInput,
    AgentResourceFilter,
    AgentResourceOrder,
    ResourceAllocationFilter,
    ResourceAllocationOrder,
    ResourceSlotTypeFilter,
    ResourceSlotTypeOrder,
)
from ai.backend.common.dto.manager.v2.resource_slot.response import (
    AdminSearchAgentResourcesPayload,
    AdminSearchResourceAllocationsPayload,
    AdminSearchResourceSlotTypesPayload,
    AgentResourceNode,
    ResourceAllocationNode,
    ResourceSlotTypeNode,
)
from ai.backend.common.dto.manager.v2.resource_slot.types import NumberFormatInfo
from ai.backend.manager.data.resource_slot.types import (
    AgentResourceData,
    ResourceAllocationData,
    ResourceSlotTypeData,
)
from ai.backend.manager.models.resource_slot.conditions import (
    AgentResourceConditions,
    ResourceAllocationConditions,
    ResourceSlotTypeConditions,
)
from ai.backend.manager.models.resource_slot.orders import (
    AGENT_RESOURCE_DEFAULT_FORWARD_ORDER,
    AGENT_RESOURCE_TIEBREAKER_ORDER,
    RESOURCE_ALLOCATION_DEFAULT_FORWARD_ORDER,
    RESOURCE_ALLOCATION_TIEBREAKER_ORDER,
    SLOT_TYPE_DEFAULT_FORWARD_ORDER,
    SLOT_TYPE_TIEBREAKER_ORDER,
    resolve_agent_resource_order,
    resolve_resource_allocation_order,
    resolve_slot_type_order,
)
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    OffsetPagination,
    QueryCondition,
    QueryOrder,
)
from ai.backend.manager.services.resource_slot.actions.search_agent_resources import (
    SearchAgentResourcesAction,
)
from ai.backend.manager.services.resource_slot.actions.search_resource_allocations import (
    SearchResourceAllocationsAction,
)
from ai.backend.manager.services.resource_slot.actions.search_resource_slot_types import (
    SearchResourceSlotTypesAction,
)

from .base import BaseAdapter

DEFAULT_PAGINATION_LIMIT = 10


class ResourceSlotAdapter(BaseAdapter):
    """Adapter for resource slot domain operations."""

    # -------------------------------------------------------------------------
    # ResourceSlotType search
    # -------------------------------------------------------------------------

    async def search_slot_types(
        self,
        input: AdminSearchResourceSlotTypesInput,
    ) -> AdminSearchResourceSlotTypesPayload:
        """Search resource slot types with filters, orders, and pagination.

        Args:
            input: Pydantic DTO with filter, order, and pagination parameters.

        Returns:
            Pydantic payload with items and pagination info.
        """
        querier = self._build_slot_type_querier(input)

        action_result = (
            await self._processors.resource_slot.search_resource_slot_types.wait_for_complete(
                SearchResourceSlotTypesAction(querier=querier)
            )
        )

        return AdminSearchResourceSlotTypesPayload(
            items=[self._slot_type_data_to_node(item) for item in action_result.items],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    def _build_slot_type_querier(self, input: AdminSearchResourceSlotTypesInput) -> BatchQuerier:
        """Build a BatchQuerier for resource slot type search."""
        conditions = self._convert_slot_type_filter(input.filter) if input.filter else []
        orders = (
            self._convert_slot_type_orders(input.order)
            if input.order
            else [SLOT_TYPE_DEFAULT_FORWARD_ORDER]
        )
        orders.append(SLOT_TYPE_TIEBREAKER_ORDER)
        pagination = self._build_slot_type_pagination(input)
        return BatchQuerier(conditions=conditions, orders=orders, pagination=pagination)

    def _convert_slot_type_filter(self, filter: ResourceSlotTypeFilter) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
        if filter.slot_name is not None:
            condition = self._convert_slot_name_filter_for_slot_type(filter.slot_name)
            if condition is not None:
                conditions.append(condition)
        return conditions

    def _convert_slot_name_filter_for_slot_type(self, sf: StringFilter) -> QueryCondition | None:
        return self.convert_string_filter(
            sf,
            contains_factory=ResourceSlotTypeConditions.by_slot_name_contains,
            equals_factory=ResourceSlotTypeConditions.by_slot_name_equals,
            starts_with_factory=ResourceSlotTypeConditions.by_slot_name_starts_with,
            ends_with_factory=ResourceSlotTypeConditions.by_slot_name_ends_with,
        )

    @staticmethod
    def _convert_slot_type_orders(orders: list[ResourceSlotTypeOrder]) -> list[QueryOrder]:
        return [resolve_slot_type_order(o.field, o.direction) for o in orders]

    @staticmethod
    def _build_slot_type_pagination(
        input: AdminSearchResourceSlotTypesInput,
    ) -> OffsetPagination:
        return OffsetPagination(
            limit=input.limit if input.limit is not None else DEFAULT_PAGINATION_LIMIT,
            offset=input.offset if input.offset is not None else 0,
        )

    @staticmethod
    def _slot_type_data_to_node(data: ResourceSlotTypeData) -> ResourceSlotTypeNode:
        """Convert ResourceSlotTypeData to Pydantic DTO node."""
        return ResourceSlotTypeNode(
            id=data.slot_name,
            slot_name=data.slot_name,
            slot_type=data.slot_type,
            display_name=data.display_name,
            description=data.description,
            display_unit=data.display_unit,
            display_icon=data.display_icon,
            number_format=NumberFormatInfo(
                binary=data.number_format.binary,
                round_length=data.number_format.round_length,
            ),
            rank=data.rank,
        )

    # -------------------------------------------------------------------------
    # AgentResource search
    # -------------------------------------------------------------------------

    async def search_agent_resources(
        self,
        input: AdminSearchAgentResourcesInput,
    ) -> AdminSearchAgentResourcesPayload:
        """Search agent resources with filters, orders, and pagination.

        Args:
            input: Pydantic DTO with filter, order, and pagination parameters.

        Returns:
            Pydantic payload with items and pagination info.
        """
        querier = self._build_agent_resource_querier(input)

        action_result = (
            await self._processors.resource_slot.search_agent_resources.wait_for_complete(
                SearchAgentResourcesAction(querier=querier)
            )
        )

        return AdminSearchAgentResourcesPayload(
            items=[self._agent_resource_data_to_node(item) for item in action_result.items],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    def _build_agent_resource_querier(self, input: AdminSearchAgentResourcesInput) -> BatchQuerier:
        """Build a BatchQuerier for agent resource search."""
        conditions = self._convert_agent_resource_filter(input.filter) if input.filter else []
        orders = (
            self._convert_agent_resource_orders(input.order)
            if input.order
            else [AGENT_RESOURCE_DEFAULT_FORWARD_ORDER]
        )
        orders.append(AGENT_RESOURCE_TIEBREAKER_ORDER)
        pagination = self._build_agent_resource_pagination(input)
        return BatchQuerier(conditions=conditions, orders=orders, pagination=pagination)

    def _convert_agent_resource_filter(self, filter: AgentResourceFilter) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
        if filter.slot_name is not None:
            condition = self._convert_slot_name_filter_for_agent_resource(filter.slot_name)
            if condition is not None:
                conditions.append(condition)
        if filter.agent_id is not None:
            condition = self._convert_agent_id_filter(filter.agent_id)
            if condition is not None:
                conditions.append(condition)
        return conditions

    def _convert_slot_name_filter_for_agent_resource(
        self, sf: StringFilter
    ) -> QueryCondition | None:
        return self.convert_string_filter(
            sf,
            contains_factory=AgentResourceConditions.by_slot_name_contains,
            equals_factory=AgentResourceConditions.by_slot_name_equals,
            starts_with_factory=AgentResourceConditions.by_slot_name_starts_with,
            ends_with_factory=AgentResourceConditions.by_slot_name_ends_with,
        )

    def _convert_agent_id_filter(self, sf: StringFilter) -> QueryCondition | None:
        return self.convert_string_filter(
            sf,
            contains_factory=AgentResourceConditions.by_agent_id_contains,
            equals_factory=AgentResourceConditions.by_agent_id_equals,
            starts_with_factory=AgentResourceConditions.by_agent_id_starts_with,
            ends_with_factory=AgentResourceConditions.by_agent_id_ends_with,
        )

    @staticmethod
    def _convert_agent_resource_orders(orders: list[AgentResourceOrder]) -> list[QueryOrder]:
        return [resolve_agent_resource_order(o.field, o.direction) for o in orders]

    @staticmethod
    def _build_agent_resource_pagination(
        input: AdminSearchAgentResourcesInput,
    ) -> OffsetPagination:
        return OffsetPagination(
            limit=input.limit if input.limit is not None else DEFAULT_PAGINATION_LIMIT,
            offset=input.offset if input.offset is not None else 0,
        )

    @staticmethod
    def _agent_resource_data_to_node(data: AgentResourceData) -> AgentResourceNode:
        """Convert AgentResourceData to Pydantic DTO node."""
        return AgentResourceNode(
            id=f"{data.agent_id}:{data.slot_name}",
            agent_id=data.agent_id,
            slot_name=data.slot_name,
            capacity=str(data.capacity),
            occupied=str(data.used),
        )

    # -------------------------------------------------------------------------
    # ResourceAllocation search
    # -------------------------------------------------------------------------

    async def search_allocations(
        self,
        input: AdminSearchResourceAllocationsInput,
    ) -> AdminSearchResourceAllocationsPayload:
        """Search resource allocations with filters, orders, and pagination.

        Args:
            input: Pydantic DTO with filter, order, and pagination parameters.

        Returns:
            Pydantic payload with items and pagination info.
        """
        querier = self._build_resource_allocation_querier(input)

        action_result = (
            await self._processors.resource_slot.search_resource_allocations.wait_for_complete(
                SearchResourceAllocationsAction(querier=querier)
            )
        )

        return AdminSearchResourceAllocationsPayload(
            items=[self._resource_allocation_data_to_node(item) for item in action_result.items],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    def _build_resource_allocation_querier(
        self, input: AdminSearchResourceAllocationsInput
    ) -> BatchQuerier:
        """Build a BatchQuerier for resource allocation search."""
        conditions = self._convert_resource_allocation_filter(input.filter) if input.filter else []
        orders = (
            self._convert_resource_allocation_orders(input.order)
            if input.order
            else [RESOURCE_ALLOCATION_DEFAULT_FORWARD_ORDER]
        )
        orders.append(RESOURCE_ALLOCATION_TIEBREAKER_ORDER)
        pagination = self._build_resource_allocation_pagination(input)
        return BatchQuerier(conditions=conditions, orders=orders, pagination=pagination)

    def _convert_resource_allocation_filter(
        self, filter: ResourceAllocationFilter
    ) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
        if filter.slot_name is not None:
            condition = self._convert_slot_name_filter_for_allocation(filter.slot_name)
            if condition is not None:
                conditions.append(condition)
        if filter.kernel_id is not None:
            condition = self._convert_kernel_id_filter(filter.kernel_id)
            if condition is not None:
                conditions.append(condition)
        return conditions

    def _convert_slot_name_filter_for_allocation(self, sf: StringFilter) -> QueryCondition | None:
        return self.convert_string_filter(
            sf,
            contains_factory=ResourceAllocationConditions.by_slot_name_contains,
            equals_factory=ResourceAllocationConditions.by_slot_name_equals,
            starts_with_factory=ResourceAllocationConditions.by_slot_name_starts_with,
            ends_with_factory=ResourceAllocationConditions.by_slot_name_ends_with,
        )

    def _convert_kernel_id_filter(self, uf: UUIDFilter) -> QueryCondition | None:
        return self.convert_uuid_filter(
            uf,
            equals_factory=ResourceAllocationConditions.by_kernel_id_filter_equals,
            in_factory=ResourceAllocationConditions.by_kernel_id_filter_in,
        )

    @staticmethod
    def _convert_resource_allocation_orders(
        orders: list[ResourceAllocationOrder],
    ) -> list[QueryOrder]:
        return [resolve_resource_allocation_order(o.field, o.direction) for o in orders]

    @staticmethod
    def _build_resource_allocation_pagination(
        input: AdminSearchResourceAllocationsInput,
    ) -> OffsetPagination:
        return OffsetPagination(
            limit=input.limit if input.limit is not None else DEFAULT_PAGINATION_LIMIT,
            offset=input.offset if input.offset is not None else 0,
        )

    @staticmethod
    def _resource_allocation_data_to_node(data: ResourceAllocationData) -> ResourceAllocationNode:
        """Convert ResourceAllocationData to Pydantic DTO node."""
        return ResourceAllocationNode(
            id=f"{data.kernel_id}:{data.slot_name}",
            kernel_id=str(data.kernel_id),
            slot_name=data.slot_name,
            requested=str(data.requested),
            used=str(data.used) if data.used is not None else None,
        )
