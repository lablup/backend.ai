"""Resource slot adapter bridging DTOs and Processors."""

from __future__ import annotations

import uuid
from functools import lru_cache
from typing import assert_never

from ai.backend.common.data.entity.agent import AgentUUID
from ai.backend.common.data.entity.domain import DomainName
from ai.backend.common.data.entity.kernel import KernelID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.session import SessionID
from ai.backend.common.dto.manager.defs import DEFAULT_PAGE_LIMIT
from ai.backend.common.dto.manager.v2.fair_share.types import (
    ResourceSlotEntryInfo,
    ResourceSlotInfo,
)
from ai.backend.common.dto.manager.v2.resource_slot.request import (
    AdminSearchAgentResourcesInput,
    AdminSearchResourceAllocationsInput,
    AdminSearchResourceSlotTypesInput,
    AgentResourceFilter,
    AgentResourceOrder,
    CreateResourceSlotTypeInput,
    PurgeResourceSlotTypeInput,
    ResourceAllocationFilter,
    ResourceAllocationOrder,
    ResourceSlotTypeFilter,
    ResourceSlotTypeOrder,
    ScopedSearchAgentResourcesInput,
    UpdateResourceSlotTypeInput,
)
from ai.backend.common.dto.manager.v2.resource_slot.response import (
    ActiveResourceOverviewInfoDTO,
    AdminSearchAgentResourcesPayload,
    AdminSearchResourceAllocationsPayload,
    AdminSearchResourceSlotTypesPayload,
    AgentResourceNode,
    CreateResourceSlotTypePayload,
    PurgeResourceSlotTypePayload,
    ResourceAllocationNode,
    ResourceSlotTypeNode,
    UpdateResourceSlotTypePayload,
)
from ai.backend.common.dto.manager.v2.resource_slot.types import (
    AgentResourceOrderField,
    NumberFormatInfo,
    NumberFormatInput,
    OrderDirection,
    ResourceAllocationOrderField,
    ResourceSlotTypeOrderField,
)
from ai.backend.common.types import AgentId
from ai.backend.manager.api.adapter_options.pagination.pagination import PaginationSpec
from ai.backend.manager.api.adapters.base import BaseAdapter
from ai.backend.manager.data.resource_slot.types import (
    AgentResourceData,
    ResourceAllocationData,
    ResourceSlotTypeData,
)
from ai.backend.manager.models.clauses import QueryCondition, QueryOrder
from ai.backend.manager.models.resource_slot.creators import ResourceSlotTypeCreator
from ai.backend.manager.models.resource_slot.purgers import ResourceSlotTypePurger
from ai.backend.manager.models.resource_slot.row import (
    AgentResourceRow,
    ResourceAllocationRow,
    ResourceSlotTypeRow,
)
from ai.backend.manager.models.resource_slot.scopes import PublicResourceSlotTypeTarget
from ai.backend.manager.models.resource_slot.searchable_fields import (
    AgentResourceSearchableFields,
    ResourceAllocationSearchableFields,
    ResourceSlotTypeSearchableFields,
)
from ai.backend.manager.models.resource_slot.searchers import (
    AgentResourceSearcher,
    ResourceAllocationSearcher,
    ResourceSlotTypeSearcher,
    UnrankedAgentResourceSearcher,
)
from ai.backend.manager.models.resource_slot.types import NumberFormat
from ai.backend.manager.models.resource_slot.updaters import ResourceSlotTypeUpdater
from ai.backend.manager.models.specs.pagination import OffsetPagination
from ai.backend.manager.models.specs.searcher import GlobalSearcher, ScopedSearcher
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.services.agent.actions.lookup import LookupAgentAction
from ai.backend.manager.services.agent.actions.scoped_search_resources import (
    ScopedSearchAgentResourcesAction,
)
from ai.backend.manager.services.agent.processors import AgentProcessors
from ai.backend.manager.services.domain.actions.lookup import LookupDomainAction
from ai.backend.manager.services.domain.processors import DomainProcessors
from ai.backend.manager.services.resource_slot.actions.create import CreateResourceSlotTypeAction
from ai.backend.manager.services.resource_slot.actions.get import GetResourceSlotTypeAction
from ai.backend.manager.services.resource_slot.actions.get_agent_resource_by_slot import (
    GetAgentResourceBySlotAction,
)
from ai.backend.manager.services.resource_slot.actions.get_domain_resource_overview import (
    GetDomainResourceOverviewAction,
)
from ai.backend.manager.services.resource_slot.actions.get_kernel_allocation_by_slot import (
    GetKernelAllocationBySlotAction,
)
from ai.backend.manager.services.resource_slot.actions.get_project_resource_overview import (
    GetProjectResourceOverviewAction,
)
from ai.backend.manager.services.resource_slot.actions.lookup import (
    LookupResourceSlotTypeAction,
)
from ai.backend.manager.services.resource_slot.actions.lookup_kernel_owner import (
    LookupKernelOwnerAction,
)
from ai.backend.manager.services.resource_slot.actions.purge import PurgeResourceSlotTypeAction
from ai.backend.manager.services.resource_slot.actions.scoped_search_resource_slot_types import (
    ScopedSearchResourceSlotTypesAction,
)
from ai.backend.manager.services.resource_slot.actions.search_agent_resources import (
    GlobalSearchAgentResourcesAction,
)
from ai.backend.manager.services.resource_slot.actions.search_resource_allocations import (
    GlobalSearchResourceAllocationsAction,
)
from ai.backend.manager.services.resource_slot.actions.update import UpdateResourceSlotTypeAction
from ai.backend.manager.services.resource_slot.processors import ResourceSlotProcessors
from ai.backend.manager.types import OptionalState


@lru_cache(maxsize=1)
def _get_slot_type_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=ResourceSlotTypeSearchableFields.own.slot_name.order.apply(ascending=True),
        cursor_column=ResourceSlotTypeRow.uuid,
    )


@lru_cache(maxsize=1)
def _get_agent_resource_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=AgentResourceSearchableFields.own.slot_name.order.apply(ascending=True),
        cursor_column=AgentResourceRow.id,
    )


@lru_cache(maxsize=1)
def _get_resource_allocation_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=ResourceAllocationSearchableFields.own.slot_name.order.apply(ascending=True),
        cursor_column=ResourceAllocationRow.id,
    )


class ResourceSlotAdapter(BaseAdapter):
    """Adapter for resource slot domain operations."""

    _resource_slot: ResourceSlotProcessors
    _agent: AgentProcessors
    _domain: DomainProcessors

    def __init__(
        self,
        resource_slot: ResourceSlotProcessors,
        agent: AgentProcessors,
        domain: DomainProcessors,
    ) -> None:
        self._resource_slot = resource_slot
        self._agent = agent
        self._domain = domain

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
        searcher = self._build_slot_type_searcher(input)

        action_result = await self._resource_slot.scoped_search_resource_slot_types.run(
            ScopedSearchResourceSlotTypesAction(
                searcher=ScopedSearcher(
                    scopes=[PublicResourceSlotTypeTarget()], used_by=(), searcher=searcher
                )
            )
        )

        return AdminSearchResourceSlotTypesPayload(
            items=[self._slot_type_data_to_node(item) for item in action_result.items],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    def _build_slot_type_searcher(
        self, input: AdminSearchResourceSlotTypesInput
    ) -> ResourceSlotTypeSearcher:
        """Build a Searcher for resource slot type search."""
        conditions = self._convert_slot_type_filter(input.filter) if input.filter else []
        orders = self._convert_slot_type_orders(input.order) if input.order else []
        return self._build_searcher(
            ResourceSlotTypeSearcher,
            pagination_spec=_get_slot_type_pagination_spec(),
            conditions=conditions,
            orders=orders,
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )

    def _convert_slot_type_filter(self, filter: ResourceSlotTypeFilter) -> list[QueryCondition]:
        fields = ResourceSlotTypeSearchableFields.own
        return self.apply_string_filter(filter.slot_name, fields.slot_name.filter)

    def _convert_slot_type_orders(self, orders: list[ResourceSlotTypeOrder]) -> list[QueryOrder]:
        fields = ResourceSlotTypeSearchableFields.own
        result: list[QueryOrder] = []
        for order in orders:
            ascending = order.direction == OrderDirection.ASC
            match order.field:
                case ResourceSlotTypeOrderField.SLOT_NAME:
                    result.append(fields.slot_name.order.apply(ascending))
                case ResourceSlotTypeOrderField.RANK:
                    result.append(fields.rank.order.apply(ascending))
                case ResourceSlotTypeOrderField.DISPLAY_NAME:
                    result.append(fields.display_name.order.apply(ascending))
        return result

    # -------------------------------------------------------------------------
    # ResourceSlotType write (superadmin only)
    # -------------------------------------------------------------------------

    async def admin_create_slot_type(
        self, input: CreateResourceSlotTypeInput
    ) -> CreateResourceSlotTypePayload:
        """Register a new resource slot type."""
        creator = ResourceSlotTypeCreator(
            slot_name=input.slot_name,
            slot_type=input.slot_type,
            required=input.required,
            enabled=input.enabled,
            display_name=input.display_name,
            description=input.description,
            display_unit=input.display_unit,
            display_icon=input.display_icon,
            number_format=self._to_number_format(input.number_format),
            rank=input.rank,
        )
        action_result = await self._resource_slot.global_create_resource_slot_type.run(
            CreateResourceSlotTypeAction(creator=creator)
        )
        return CreateResourceSlotTypePayload(
            resource_slot_type=self._slot_type_data_to_node(action_result.data),
        )

    async def admin_update_slot_type(
        self, input: UpdateResourceSlotTypeInput
    ) -> UpdateResourceSlotTypePayload:
        """Update the display and scheduling flags of a resource slot type."""
        target = await self._resource_slot.lookup_resource_slot_type.run(
            LookupResourceSlotTypeAction(slot_name=input.slot_name)
        )
        updater = ResourceSlotTypeUpdater(
            slot_type_id=target.entity_id(),
            required=OptionalState.from_nullable(input.required),
            enabled=OptionalState.from_nullable(input.enabled),
            display_name=OptionalState.from_nullable(input.display_name),
            description=OptionalState.from_nullable(input.description),
            display_unit=OptionalState.from_nullable(input.display_unit),
            display_icon=OptionalState.from_nullable(input.display_icon),
            number_format=(
                OptionalState.update(self._to_number_format(input.number_format))
                if input.number_format is not None
                else OptionalState.nop()
            ),
            rank=OptionalState.from_nullable(input.rank),
        )
        action_result = await self._resource_slot.global_update_resource_slot_type.run(
            UpdateResourceSlotTypeAction(updater=updater)
        )
        return UpdateResourceSlotTypePayload(
            resource_slot_type=self._slot_type_data_to_node(action_result.data),
        )

    async def admin_purge_slot_type(
        self, input: PurgeResourceSlotTypeInput
    ) -> PurgeResourceSlotTypePayload:
        """Remove a resource slot type, refusing while anything still references it."""
        target = await self._resource_slot.lookup_resource_slot_type.run(
            LookupResourceSlotTypeAction(slot_name=input.slot_name)
        )
        action_result = await self._resource_slot.purge_resource_slot_type.run(
            PurgeResourceSlotTypeAction(
                purger=ResourceSlotTypePurger(
                    slot_name=input.slot_name, slot_type_id=target.entity_id()
                )
            )
        )
        return PurgeResourceSlotTypePayload(slot_name=action_result.data.slot_name)

    @staticmethod
    def _to_number_format(input: NumberFormatInput | None) -> NumberFormat:
        if input is None:
            return NumberFormat()
        return NumberFormat(binary=input.binary, round_length=input.round_length)

    @staticmethod
    def _slot_type_data_to_node(data: ResourceSlotTypeData) -> ResourceSlotTypeNode:
        """Convert ResourceSlotTypeData to Pydantic DTO node."""
        return ResourceSlotTypeNode(
            id=data.slot_name,
            entity_id=data.entity_id(),
            uuid=data.uuid,
            slot_name=data.slot_name,
            slot_type=data.slot_type,
            required=data.required,
            enabled=data.enabled,
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

        action_result = await self._resource_slot.search_agent_resources.run(
            GlobalSearchAgentResourcesAction(
                searcher=GlobalSearcher(
                    used_by=(),
                    searcher=UnrankedAgentResourceSearcher(
                        pagination=querier.pagination,
                        conditions=querier.conditions,
                        orders=querier.orders,
                    ),
                )
            )
        )

        return AdminSearchAgentResourcesPayload(
            items=[self._agent_resource_data_to_node(item) for item in action_result.items],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    async def scoped_search_agent_resources(
        self,
        input: ScopedSearchAgentResourcesInput,
    ) -> AdminSearchAgentResourcesPayload:
        """Read the slot rows the named agents carry, combined with OR."""
        conditions = self._convert_agent_resource_filter(input.filter) if input.filter else []
        orders = self._convert_agent_resource_orders(input.order) if input.order else []
        result = await self._agent.scoped_search_resources.run(
            ScopedSearchAgentResourcesAction(
                agent_uuids=[AgentUUID(entry.value) for entry in input.scope.agent or ()],
                searcher=AgentResourceSearcher(
                    conditions=conditions,
                    orders=orders,
                    pagination=OffsetPagination(
                        limit=input.limit or DEFAULT_PAGE_LIMIT, offset=input.offset or 0
                    ),
                ),
            )
        )
        return AdminSearchAgentResourcesPayload(
            items=[self._agent_resource_data_to_node(item) for item in result.items],
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    def _build_agent_resource_querier(self, input: AdminSearchAgentResourcesInput) -> BatchQuerier:
        """Build a BatchQuerier for agent resource search."""
        conditions = self._convert_agent_resource_filter(input.filter) if input.filter else []
        orders = self._convert_agent_resource_orders(input.order) if input.order else []
        return self._build_querier(
            pagination_spec=_get_agent_resource_pagination_spec(),
            conditions=conditions,
            orders=orders,
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )

    def _convert_agent_resource_filter(self, filter: AgentResourceFilter) -> list[QueryCondition]:
        fields = AgentResourceSearchableFields.own
        return [
            *self.apply_string_filter(filter.slot_name, fields.slot_name.filter),
            *self.apply_string_filter(filter.agent_id, fields.agent_id.filter),
        ]

    @staticmethod
    def _convert_agent_resource_orders(orders: list[AgentResourceOrder]) -> list[QueryOrder]:
        fields = AgentResourceSearchableFields.own
        converted: list[QueryOrder] = []
        for o in orders:
            ascending = o.direction == OrderDirection.ASC
            match o.field:
                case AgentResourceOrderField.AGENT_ID:
                    converted.append(fields.agent_id.order.apply(ascending))
                case AgentResourceOrderField.SLOT_NAME:
                    converted.append(fields.slot_name.order.apply(ascending))
                case AgentResourceOrderField.CAPACITY:
                    converted.append(fields.capacity.order.apply(ascending))
                case AgentResourceOrderField.USED:
                    converted.append(fields.used.order.apply(ascending))
                case _:
                    assert_never(o.field)
        return converted

    @staticmethod
    def _agent_resource_data_to_node(data: AgentResourceData) -> AgentResourceNode:
        """Convert AgentResourceData to Pydantic DTO node."""
        return AgentResourceNode(
            id=f"{data.agent_id}:{data.slot_name}",
            field_id=data.id,
            agent_id=data.agent_id,
            slot_name=data.slot_name,
            capacity=str(data.capacity),
            used=str(data.used),
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

        action_result = await self._resource_slot.search_resource_allocations.run(
            GlobalSearchResourceAllocationsAction(
                searcher=GlobalSearcher(
                    used_by=(),
                    searcher=ResourceAllocationSearcher(
                        pagination=querier.pagination,
                        conditions=querier.conditions,
                        orders=querier.orders,
                    ),
                )
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
        orders = self._convert_resource_allocation_orders(input.order) if input.order else []
        return self._build_querier(
            pagination_spec=_get_resource_allocation_pagination_spec(),
            conditions=conditions,
            orders=orders,
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )

    def _convert_resource_allocation_filter(
        self, filter: ResourceAllocationFilter
    ) -> list[QueryCondition]:
        fields = ResourceAllocationSearchableFields.own
        return [
            *self.apply_string_filter(filter.slot_name, fields.slot_name.filter),
            *self.apply_uuid_filter(filter.kernel_id, fields.kernel_id.filter),
        ]

    @staticmethod
    def _convert_resource_allocation_orders(
        orders: list[ResourceAllocationOrder],
    ) -> list[QueryOrder]:
        fields = ResourceAllocationSearchableFields.own
        converted: list[QueryOrder] = []
        for o in orders:
            ascending = o.direction == OrderDirection.ASC
            match o.field:
                case ResourceAllocationOrderField.KERNEL_ID:
                    converted.append(fields.kernel_id.order.apply(ascending))
                case ResourceAllocationOrderField.SLOT_NAME:
                    converted.append(fields.slot_name.order.apply(ascending))
                case ResourceAllocationOrderField.REQUESTED:
                    converted.append(fields.requested.order.apply(ascending))
                case ResourceAllocationOrderField.USED:
                    converted.append(fields.used.order.apply(ascending))
                case _:
                    assert_never(o.field)
        return converted

    @staticmethod
    def _resource_allocation_data_to_node(data: ResourceAllocationData) -> ResourceAllocationNode:
        """Convert ResourceAllocationData to Pydantic DTO node."""
        return ResourceAllocationNode(
            id=f"{data.kernel_id}:{data.slot_name}",
            field_id=data.id,
            kernel_id=str(data.kernel_id),
            slot_name=data.slot_name,
            requested=str(data.requested),
            used=str(data.used) if data.used is not None else None,
        )

    # -------------------------------------------------------------------------
    # Single-item getters
    # -------------------------------------------------------------------------

    async def get_slot_type(self, slot_name: str) -> ResourceSlotTypeNode:
        """Retrieve a single resource slot type by slot name."""
        resolved = await self._resource_slot.lookup_resource_slot_type.run(
            LookupResourceSlotTypeAction(slot_name=slot_name)
        )
        action_result = await self._resource_slot.get_resource_slot_type.run(
            GetResourceSlotTypeAction(slot_type_id=resolved.entity_id())
        )
        return self._slot_type_data_to_node(action_result.data)

    async def get_agent_resource(self, agent_id: str, slot_name: str) -> AgentResourceNode:
        """Retrieve a single agent resource by agent ID and slot name."""
        agent = await self._agent.lookup.run(LookupAgentAction(agent_id=AgentId(agent_id)))
        action_result = await self._resource_slot.get_agent_resource_by_slot.run(
            GetAgentResourceBySlotAction(
                agent_uuid=agent.entity_id(), agent_id=agent_id, slot_name=slot_name
            )
        )
        return self._agent_resource_data_to_node(action_result.item)

    async def get_kernel_allocation(
        self, kernel_id: uuid.UUID, slot_name: str
    ) -> ResourceAllocationNode:
        """Retrieve a single kernel resource allocation by kernel ID and slot name."""
        owner = await self._resource_slot.lookup_kernel_owner.run(
            LookupKernelOwnerAction(kernel_id=KernelID(kernel_id))
        )
        action_result = await self._resource_slot.get_kernel_allocation_by_slot.run(
            GetKernelAllocationBySlotAction(
                session_id=SessionID(owner.entity_id()),
                kernel_id=KernelID(kernel_id),
                slot_name=slot_name,
            )
        )
        return self._resource_allocation_data_to_node(action_result.item)

    # -------------------------------------------------------------------------
    # Resource overview
    # -------------------------------------------------------------------------

    async def get_domain_resource_overview(self, domain_name: str) -> ActiveResourceOverviewInfoDTO:
        """Retrieve active resource occupancy overview for a domain."""
        domain = await self._domain.lookup.run(LookupDomainAction(name=DomainName(domain_name)))
        action_result = await self._resource_slot.get_domain_resource_overview.run(
            GetDomainResourceOverviewAction(domain_id=domain.entity_id(), domain_name=domain_name)
        )
        occupancy = action_result.item
        return ActiveResourceOverviewInfoDTO(
            slots=ResourceSlotInfo(
                entries=[
                    ResourceSlotEntryInfo(
                        resource_type=sq.slot_name,
                        quantity=sq.quantity,
                    )
                    for sq in occupancy.used_slots
                ]
            ),
            session_count=occupancy.session_count,
        )

    async def get_project_resource_overview(
        self, project_id: uuid.UUID
    ) -> ActiveResourceOverviewInfoDTO:
        """Retrieve active resource occupancy overview for a project."""
        action_result = await self._resource_slot.get_project_resource_overview.run(
            GetProjectResourceOverviewAction(project_id=ProjectID(project_id))
        )
        occupancy = action_result.item
        return ActiveResourceOverviewInfoDTO(
            slots=ResourceSlotInfo(
                entries=[
                    ResourceSlotEntryInfo(
                        resource_type=sq.slot_name,
                        quantity=sq.quantity,
                    )
                    for sq in occupancy.used_slots
                ]
            ),
            session_count=occupancy.session_count,
        )
