from datetime import datetime
from enum import StrEnum
from typing import Optional

import strawberry
from strawberry.relay import Node, NodeID
from strawberry.scalars import JSON

from ai.backend.manager.api.gql.base import OrderDirection, StringFilter
from ai.backend.manager.data.agent.types import AgentStatus
from ai.backend.manager.models.rbac.permission_defs import AgentPermission
from ai.backend.manager.repositories.agent.options import AgentConditions, AgentOrders
from ai.backend.manager.repositories.base import (
    QueryCondition,
    QueryOrder,
    combine_conditions_or,
    negate_conditions,
)


@strawberry.enum(description="Fields by which agents can be ordered")
class AgentOrderField(StrEnum):
    ID = "id"
    FIRST_CONTACT = "first_contact"
    SCALING_GROUP = "scaling_group"
    SCHEDULABLE = "schedulable"


@strawberry.input(description="Filter options for agent statuses")
class AgentStatusFilter:
    in_: Optional[list[AgentStatus]] = strawberry.field(name="in", default=None)
    equals: Optional[AgentStatus] = None


@strawberry.input(description="Filter options for querying agents")
class AgentFilter:
    id: Optional[StringFilter] = None
    status: Optional[AgentStatusFilter] = None
    schedulable: Optional[bool] = None

    AND: Optional[list["AgentFilter"]] = None
    OR: Optional[list["AgentFilter"]] = None
    NOT: Optional[list["AgentFilter"]] = None

    def build_conditions(self) -> list[QueryCondition]:
        field_conditions: list[QueryCondition] = []
        if self.id is not None:
            name_condition = self.id.build_query_condition(
                contains_factory=AgentConditions.by_id_contains,
                equals_factory=AgentConditions.by_id_equals,
            )
            if name_condition is not None:
                field_conditions.append(name_condition)
        if self.status is not None:
            if self.status.in_ is not None:
                field_conditions.append(AgentConditions.by_status_contains(self.status.in_))
            if self.status.equals is not None:
                field_conditions.append(AgentConditions.by_status_equals(self.status.equals))
        if self.schedulable is not None:
            field_conditions.append(AgentConditions.by_schedulable(self.schedulable))

        if self.AND:
            for sub_filter in self.AND:
                field_conditions.extend(sub_filter.build_conditions())

        # Handle OR logical operator
        if self.OR:
            or_sub_conditions: list[QueryCondition] = []
            for sub_filter in self.OR:
                or_sub_conditions.extend(sub_filter.build_conditions())
            if or_sub_conditions:
                field_conditions.append(combine_conditions_or(or_sub_conditions))

        # Handle NOT logical operator
        if self.NOT:
            not_sub_conditions: list[QueryCondition] = []
            for sub_filter in self.NOT:
                not_sub_conditions.extend(sub_filter.build_conditions())
            if not_sub_conditions:
                field_conditions.append(negate_conditions(not_sub_conditions))

        return field_conditions


@strawberry.input
class AgentOrderBy:
    field: AgentOrderField
    direction: OrderDirection = OrderDirection.ASC

    def to_query_order(self) -> QueryOrder:
        ascending = self.direction == OrderDirection.ASC
        match self.field:
            case AgentOrderField.ID:
                return AgentOrders.id(ascending)
            case AgentOrderField.FIRST_CONTACT:
                return AgentOrders.first_contact(ascending)
            case AgentOrderField.SCALING_GROUP:
                return AgentOrders.scaling_group(ascending)
            case AgentOrderField.SCHEDULABLE:
                return AgentOrders.schedulable(ascending)


@strawberry.type(description="Added in 25.15.0")
class AgentResource:
    free: JSON
    used: JSON
    capacity: JSON


@strawberry.type(description="Added in 25.15.0")
class AgentStats:
    total_resource: AgentResource = strawberry.field(description="Added in 25.15.0")


@strawberry.type(description="Status and lifecycle information for an agent")
class AgentStatusInfo:
    status: AgentStatus
    status_changed: datetime
    first_contact: datetime
    lost_at: Optional[datetime]
    schedulable: bool


@strawberry.type(description="System and configuration information for an agent")
class AgentSystemInfo:
    architecture: str
    version: str
    auto_terminate_abusing_kernel: bool = strawberry.field(
        description="Not used anymore, present for schema consistency."
    )
    compute_plugins: JSON


@strawberry.type(description="Network-related information for an agent")
class AgentNetworkInfo:
    region: str
    addr: str = strawberry.field(
        description="Agent's address with port. (bind/advertised host:port)"
    )


@strawberry.type(description="Strawberry-based Agent type replacing AgentNode. Added in 25.18.0.")
class AgentV2(Node):
    id: NodeID[str]
    resource_info: AgentResource
    status_info: AgentStatusInfo
    system_info: AgentSystemInfo
    network_info: AgentNetworkInfo
    permissions: list[AgentPermission]
    scaling_group: str
